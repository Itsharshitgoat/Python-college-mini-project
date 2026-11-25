"""Mouse-wheel compatibility fixes for CustomTkinter on macOS.

CustomTkinter scrolls by ``event.delta`` units. On macOS a physical wheel
notch can report a delta of 1, which only moves a few pixels, while trackpad
gestures report a usable delta. This patch normalizes the step size and skips
widgets that already scroll themselves, such as tables and text boxes.
"""

from __future__ import annotations

import sys

from customtkinter.windows.widgets.ctk_scrollable_frame import CTkScrollableFrame

_INSTALLED = False

# Widgets with their own native wheel handling should not also scroll the
# surrounding screen.
_NATIVE_SCROLLERS = {"Treeview", "Text", "Listbox", "Spinbox"}


def is_scroll_fix_installed() -> bool:
    return _INSTALLED or bool(
        getattr(CTkScrollableFrame._mouse_wheel_all, "_eventra_scroll_fix", False)
    )


def install_scroll_fixes() -> bool:
    """Patch CTkScrollableFrame once. Returns True when the patch was applied."""
    global _INSTALLED
    if is_scroll_fix_installed():
        return False

    original = CTkScrollableFrame._mouse_wheel_all

    def _eventra_mouse_wheel_all(self, event):
        if not self.check_if_master_is_canvas(event.widget):
            return
        if sys.platform != "darwin":
            original(self, event)
            return

        try:
            if event.widget.winfo_class() in _NATIVE_SCROLLERS:
                return
        except Exception:
            pass

        canvas = self._parent_canvas
        if getattr(self, "_shift_pressed", False):
            if canvas.xview() != (0.0, 1.0):
                canvas.xview("scroll", -_step(event.delta), "units")
            return
        if canvas.yview() != (0.0, 1.0):
            canvas.yview("scroll", -_step(event.delta), "units")

    def _step(delta) -> int:
        try:
            value = int(delta)
        except (TypeError, ValueError):
            return 0
        if value == 0:
            return 0
        # One notch is often 1 on macOS. Four units at 8px/increment gives a
        # useful ~32px step; large trackpad deltas are clamped to avoid jumps.
        magnitude = min(abs(value), 4) * 4
        return magnitude if value > 0 else -magnitude

    _eventra_mouse_wheel_all._eventra_original = original
    _eventra_mouse_wheel_all._eventra_scroll_fix = True
    CTkScrollableFrame._mouse_wheel_all = _eventra_mouse_wheel_all
    _INSTALLED = True
    return True
