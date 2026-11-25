"""QR check-in scanner with a background camera worker thread."""

from __future__ import annotations

import queue
import threading
import time

import cv2
import customtkinter as ctk
import numpy as np
from PIL import Image

from hardware.camera import Camera
from hardware.camera_access import (
    CameraPermission,
    camera_access_message,
    camera_permission_status,
    is_eventra_app_bundle,
    open_camera_settings,
    request_camera_permission,
)
from hardware.qr_decoder import QrDecoder
from ui.components.notification import notify
from ui.screens.base import ScreenBase
from ui.theme import (
    BORDER, ERROR, ERROR_BG, MUTED, NAVY, SUCCESS, SUCCESS_BG, SURFACE, TEXT,
    WARNING, WARNING_BG, button_style, card_style, font,
)
from utils.date_utils import format_time, utc_now_iso
from utils.result import ResultCode


class CameraWorker(threading.Thread):
    def __init__(self, camera: Camera, decoder: QrDecoder, frames: queue.Queue,
                 payloads: queue.Queue, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.camera = camera
        self.decoder = decoder
        self.frames = frames
        self.payloads = payloads
        self.stop_event = stop_event

    def run(self) -> None:
        try:
            while not self.stop_event.is_set():
                ok, frame = self.camera.read()
                if not ok or frame is None:
                    time.sleep(0.05)
                    continue
                payload, points = self.decoder.decode(frame)
                display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                display = QrDecoder.draw_marker(display, points)
                display = cv2.resize(display, (640, 420))

                while not self.frames.empty():
                    try:
                        self.frames.get_nowait()
                    except queue.Empty:
                        break
                self.frames.put(display)

                if payload:
                    while not self.payloads.empty():
                        try:
                            self.payloads.get_nowait()
                        except queue.Empty:
                            break
                    self.payloads.put(payload)
                time.sleep(0.035)
        finally:
            self.camera.close()


class ScannerScreen(ScreenBase):
    def __init__(self, master, ctx, nav, event_id: int | None = None, **kwargs):
        super().__init__(master, ctx, nav, "QR Check-in", "Scan participant tickets for entry")
        self.initial_event_id = event_id
        self.event_ids: dict[str, int] = {}
        self.worker: CameraWorker | None = None
        self.stop_event: threading.Event | None = None
        self.frames: queue.Queue = queue.Queue(maxsize=1)
        self.payloads: queue.Queue = queue.Queue(maxsize=1)
        self._photo = None
        self._scan_ready_at = 0.0
        self._result_serial = 0
        self._running = True
        self._polling = False
        self._poll_after: str | None = None
        self._reset_after: str | None = None

        top = ctk.CTkFrame(self.body, **card_style())
        top.pack(fill="x")
        top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            top, text="EVENT", font=font(11, "bold"), text_color=MUTED, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.event_var = ctk.StringVar()
        self.event_combo = ctk.CTkComboBox(
            top, values=["Loading..."], variable=self.event_var,
            state="readonly", height=38, font=font(13),
            command=lambda *_: self._event_changed(),
        )
        self.event_combo.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        self.event_info = ctk.CTkLabel(
            top, text="Select an event", font=font(12), text_color=MUTED, anchor="w",
            justify="left",
        )
        self.event_info.grid(row=0, column=1, rowspan=2, sticky="w", padx=20)

        content = ctk.CTkFrame(self.body, fg_color="transparent")
        content.pack(fill="both", expand=True, pady=(14, 0))
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(0, weight=1)

        camera_card = ctk.CTkFrame(content, **card_style())
        camera_card.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(
            camera_card, text="CAMERA FEED", font=font(11, "bold"),
            text_color=MUTED, anchor="w",
        ).pack(anchor="w", padx=16, pady=(14, 8))
        self.camera_label = ctk.CTkLabel(
            camera_card, text="Camera is off\n\nClick 'Start Camera' to begin scanning",
            font=font(13), text_color=MUTED, corner_radius=12,
            fg_color="#0F172A", width=648, height=426,
            wraplength=620, justify="center",
        )
        self.camera_label.pack(padx=14)
        camera_buttons = ctk.CTkFrame(camera_card, fg_color="transparent")
        camera_buttons.pack(fill="x", padx=14, pady=14)
        self.start_btn = ctk.CTkButton(
            camera_buttons, text="▶ Start Camera", height=38, font=font(12, "bold"),
            command=self.start_camera, **button_style("primary"),
        )
        self.start_btn.pack(side="left", padx=(0, 8))
        self.stop_btn = ctk.CTkButton(
            camera_buttons, text="■ Stop Camera", height=38, font=font(12, "bold"),
            command=self.stop_camera, state="disabled", **button_style("outline"),
        )
        self.stop_btn.pack(side="left")
        ctk.CTkButton(
            camera_buttons, text="Camera Help", height=38, font=font(11, "bold"),
            command=self._camera_help, **button_style("outline"),
        ).pack(side="left", padx=(8, 0))

        side = ctk.CTkFrame(content, fg_color="transparent")
        side.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        side.grid_rowconfigure(0, weight=1)

        self.result_card = ctk.CTkFrame(
            side, fg_color=SURFACE, corner_radius=14, border_width=2, border_color=BORDER
        )
        self.result_card.grid(row=0, column=0, sticky="nsew")
        self.result_icon = ctk.CTkLabel(
            self.result_card, text="◎", font=font(40, "bold"), text_color=NAVY
        )
        self.result_icon.pack(pady=(32, 6))
        self.result_title = ctk.CTkLabel(
            self.result_card, text="READY TO SCAN", font=font(18, "bold"),
            text_color=TEXT,
        )
        self.result_title.pack()
        self.result_message = ctk.CTkLabel(
            self.result_card, text="Present a QR ticket to the camera",
            font=font(12), text_color=MUTED, wraplength=280, justify="center",
        )
        self.result_message.pack(padx=20, pady=(8, 24))
        self.result_detail = ctk.CTkLabel(
            self.result_card, text="", font=font(12), text_color=TEXT,
            wraplength=280, justify="center",
        )
        self.result_detail.pack(padx=20)

        stats = ctk.CTkFrame(side, **card_style())
        stats.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        self.today_label = ctk.CTkLabel(
            stats, text="Today's Check-ins: 0", font=font(13, "bold"),
            text_color=TEXT, anchor="w",
        )
        self.today_label.pack(anchor="w", padx=16, pady=(14, 4))
        self.last_label = ctk.CTkLabel(
            stats, text="Last scan: -", font=font(11), text_color=MUTED, anchor="w"
        )
        self.last_label.pack(anchor="w", padx=16, pady=(0, 14))

        manual = ctk.CTkFrame(side, **card_style())
        manual.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ctk.CTkLabel(
            manual, text="MANUAL TOKEN VERIFICATION", font=font(10, "bold"),
            text_color=MUTED, anchor="w",
        ).pack(anchor="w", padx=14, pady=(12, 4))
        self.token_var = ctk.StringVar()
        ctk.CTkEntry(
            manual, placeholder_text="Paste EVENTRA ticket payload...",
            textvariable=self.token_var, height=34, font=font(11),
        ).pack(fill="x", padx=14)
        ctk.CTkButton(
            manual, text="Verify Token", height=32, font=font(11, "bold"),
            command=self._verify_manual, **button_style("secondary"),
        ).pack(fill="x", padx=14, pady=(8, 12))

        self.bind("<Destroy>", lambda _event: self._on_destroy())

    def _on_destroy(self) -> None:
        self._running = False
        for after_id in (self._poll_after, self._reset_after):
            if after_id:
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass
        self._poll_after = None
        self._reset_after = None
        self.stop_camera()

    # --- lifecycle ------------------------------------------------------
    def refresh(self):
        events = self.ctx.scanner_controller.event_options()
        labels = [f"#{event.event_id}  {event.event_name}" for event in events]
        self.event_ids = dict(zip(labels, [event.event_id for event in events]))
        self.event_combo.configure(values=labels or ["No events available"])
        if labels:
            preferred = next(
                (label for label, eid in self.event_ids.items()
                 if eid == getattr(self, "initial_event_id", None)),
                labels[0],
            )
            self.event_var.set(preferred)
        self._event_changed()
        self._show_ready()
        self._refresh_counts()

    def _event_changed(self):
        event_id = self.current_event_id()
        if not event_id:
            self.event_info.configure(text="Create and open an event first.")
            return
        result = self.ctx.event_controller.get(event_id)
        if result.success:
            event = result.data
            self.event_info.configure(
                text=f"Venue: {event.venue}\nCheck-in: {event.checkin_status}\n"
                     f"Registered: {event.registered_count}  |  Present: {event.attended_count}"
            )
        else:
            self.event_info.configure(text=result.message)

    def current_event_id(self) -> int | None:
        return self.event_ids.get(self.event_var.get())

    # --- camera ---------------------------------------------------------
    def start_camera(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.current_event_id():
            notify(self, "Select an event before starting the camera.", "warning")
            return
        if not self._ensure_camera_permission():
            return

        index = self._setting_int("camera_index", 0)
        width = self._setting_int("camera_width", 640)
        height = self._setting_int("camera_height", 480)
        camera = Camera(index, width, height)
        candidates = [index, 0, 1, 2]
        opened_index = camera.open_indices(candidates)
        if opened_index is None:
            self._show_camera_error(
                "Could not open any camera. Enable EVENTRA in Camera privacy "
                "settings, close other apps using the camera, then retry."
            )
            return
        if opened_index != index:
            self.ctx.settings_controller.set("camera_index", str(opened_index))

        self.stop_event = threading.Event()
        self.frames = queue.Queue(maxsize=1)
        self.payloads = queue.Queue(maxsize=1)
        self.worker = CameraWorker(
            camera, QrDecoder(), self.frames, self.payloads, self.stop_event
        )
        self.worker.start()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.camera_label.configure(
            text=f"Starting camera {opened_index}...", text_color="white"
        )
        self._poll()

    def _ensure_camera_permission(self) -> bool:
        status = camera_permission_status()
        if not is_eventra_app_bundle():
            self._show_camera_error(camera_access_message(status))
            return False
        if status is CameraPermission.AUTHORIZED:
            return True
        if status in (CameraPermission.DENIED, CameraPermission.RESTRICTED):
            self._show_camera_error(camera_access_message(status))
            return False
        if status is CameraPermission.NOT_DETERMINED:
            self.result_message.configure(text="Waiting for camera permission...")
            self.update_idletasks()
            granted = request_camera_permission()
            if granted is True:
                return True
            denied = (
                CameraPermission.DENIED if granted is False else CameraPermission.UNKNOWN
            )
            self._show_camera_error(camera_access_message(denied))
            return False
        return True

    def _show_camera_error(self, message: str) -> None:
        self._photo = None
        self.camera_label.configure(image=None, text=message, text_color=ERROR)
        self.result_card.configure(fg_color=ERROR_BG, border_color=ERROR)
        self.result_icon.configure(text="✕", text_color=ERROR)
        self.result_title.configure(text="CAMERA UNAVAILABLE", text_color=ERROR)
        self.result_message.configure(text=message, text_color=TEXT)
        self.result_detail.configure(
            text="You can still verify tickets with the manual token box below."
        )
        notify(self, message, "error")

    def _camera_help(self) -> None:
        if open_camera_settings():
            notify(
                self,
                "Camera privacy settings opened. Enable EVENTRA, then restart the app.",
                "warning",
            )
        else:
            notify(
                self,
                "Open System Settings > Privacy & Security > Camera and enable EVENTRA.",
                "warning",
            )

    def stop_camera(self) -> None:
        if self.stop_event:
            self.stop_event.set()
        if self._poll_after:
            try:
                self.after_cancel(self._poll_after)
            except Exception:
                pass
            self._poll_after = None
        self._polling = False
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=0.4)
        self.worker = None
        self.stop_event = None
        try:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.camera_label.configure(
                image=None,
                text="Camera is off\n\nClick 'Start Camera' to begin scanning",
                text_color=MUTED,
                font=font(13),
            )
            self._show_ready()
        except Exception:
            pass
        self._photo = None

    def _setting_int(self, key: str, default: int) -> int:
        return self.ctx.settings_controller.get_int(key, default)

    # --- polling --------------------------------------------------------
    def _poll(self) -> None:
        self._poll_after = None
        if not self._running or not self.winfo_exists():
            return
        camera_active = self.worker is not None and self.worker.is_alive()
        try:
            frame = self.frames.get_nowait()
            image = Image.fromarray(frame)
            self._photo = ctk.CTkImage(light_image=image, dark_image=image, size=(640, 420))
            self.camera_label.configure(image=self._photo, text="")
        except queue.Empty:
            pass

        if camera_active and time.time() >= self._scan_ready_at:
            try:
                payload = self.payloads.get_nowait()
                self._process_payload(payload)
            except queue.Empty:
                pass

        if camera_active:
            self._polling = True
            self._poll_after = self.after(60, self._poll)
        else:
            self._polling = False

    def _verify_manual(self) -> None:
        payload = self.token_var.get().strip()
        if not payload:
            notify(self, "Enter a QR payload to verify.", "warning")
            return
        self.token_var.set("")
        self._process_payload(payload)

    # --- verification ---------------------------------------------------
    def _process_payload(self, payload: str) -> None:
        event_id = self.current_event_id()
        if not event_id:
            notify(self, "Select an event first.", "warning")
            return
        self._scan_ready_at = time.time() + 2.5
        result = self.ctx.scanner_controller.process_scan(
            payload, event_id, self.ctx.session.user_id
        )
        self._show_result(result)
        self._refresh_counts()
        self.nav.mark_dirty("dashboard")
        self.nav.mark_dirty("attendance")
        self.nav.mark_dirty("reports")
        self.nav.mark_dirty("event_details", event_id=event_id)

    def _refresh_counts(self) -> None:
        count = self.ctx.attendance_controller.today_count()
        self.today_label.configure(text=f"Today's Check-ins: {count}")

    def _show_ready(self) -> None:
        self._result_serial += 1
        self.result_card.configure(fg_color=SURFACE, border_color=BORDER)
        self.result_icon.configure(text="◎", text_color=NAVY)
        self.result_title.configure(text="READY TO SCAN", text_color=TEXT)
        self.result_message.configure(
            text="Present a QR ticket to the camera", text_color=MUTED
        )
        self.result_detail.configure(text="")

    def _show_result(self, result) -> None:
        code = result.code
        self._result_serial += 1
        serial = self._result_serial

        if code == ResultCode.SUCCESS:
            colors = (SUCCESS_BG, SUCCESS, "✓", "CHECK-IN SUCCESSFUL", SUCCESS)
        elif code == ResultCode.ALREADY_CHECKED_IN:
            colors = (WARNING_BG, WARNING, "!", "ALREADY CHECKED IN", WARNING)
        else:
            colors = (ERROR_BG, ERROR, "✕", "ENTRY REJECTED", ERROR)
        background, border, icon, title, accent = colors
        self.result_card.configure(fg_color=background, border_color=border)
        self.result_icon.configure(text=icon, text_color=accent)
        self.result_title.configure(text=title, text_color=accent)
        self.result_message.configure(text=result.message, text_color=TEXT)

        registration = (result.data or {}).get("registration")
        if registration:
            detail = (
                f"{registration.full_name}\n{registration.code}\n"
                f"{format_time((result.data or {}).get('checked_in_at') or registration.checked_in_at)}"
            )
        else:
            detail = "No matching registration."
        self.result_detail.configure(text=detail)

        self.last_label.configure(
            text=f"Last scan: {result.message[:48]}"
        )
        if self._reset_after:
            try:
                self.after_cancel(self._reset_after)
            except Exception:
                pass
        self._reset_after = self.after(5000, lambda: self._auto_reset(serial))

    def _auto_reset(self, serial: int) -> None:
        self._reset_after = None
        if serial == self._result_serial and self.winfo_exists():
            self._show_ready()
