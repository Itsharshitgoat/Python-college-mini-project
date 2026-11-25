"""macOS camera permission helpers for EVENTRA.

The camera must be granted to a real app bundle, not a bare Python process,
otherwise macOS refuses AVFoundation capture with status 0.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from enum import Enum


class CameraPermission(str, Enum):
    NOT_DETERMINED = "not_determined"
    RESTRICTED = "restricted"
    DENIED = "denied"
    AUTHORIZED = "authorized"
    UNKNOWN = "unknown"


_AV_STATUS = {
    0: CameraPermission.NOT_DETERMINED,
    1: CameraPermission.RESTRICTED,
    2: CameraPermission.DENIED,
    3: CameraPermission.AUTHORIZED,
}


def is_eventra_app_bundle() -> bool:
    """Return True when running from EVENTRA.app (or an explicit bundle launch)."""
    if os.environ.get("EVENTRA_APP_BUNDLE") == "1":
        return True
    executable = os.path.realpath(sys.executable).replace("\\", "/")
    return ".app/Contents/MacOS/" in executable


def camera_permission_status() -> CameraPermission:
    if sys.platform != "darwin":
        return CameraPermission.UNKNOWN
    try:
        from AVFoundation import AVCaptureDevice, AVMediaTypeVideo

        raw = int(AVCaptureDevice.authorizationStatusForMediaType_(AVMediaTypeVideo))
    except Exception:
        return CameraPermission.UNKNOWN
    return _AV_STATUS.get(raw, CameraPermission.UNKNOWN)


def request_camera_permission(timeout_seconds: float = 20.0) -> bool | None:
    """Ask macOS for camera access. Returns None when the status is unavailable."""
    if sys.platform != "darwin":
        return None
    try:
        from AVFoundation import AVCaptureDevice, AVMediaTypeVideo
        from Foundation import NSDate, NSRunLoop
    except Exception:
        return None

    status = camera_permission_status()
    if status is CameraPermission.AUTHORIZED:
        return True
    if status in (CameraPermission.DENIED, CameraPermission.RESTRICTED):
        return False

    result: dict[str, bool | None] = {"granted": None}

    def completion(granted) -> None:
        result["granted"] = bool(granted)

    AVCaptureDevice.requestAccessForMediaType_completionHandler_(
        AVMediaTypeVideo, completion
    )

    deadline = time.monotonic() + timeout_seconds
    while result["granted"] is None and time.monotonic() < deadline:
        NSRunLoop.currentRunLoop().runUntilDate_(
            NSDate.dateWithTimeIntervalSinceNow_(0.1)
        )
    return result["granted"]


def open_camera_settings() -> bool:
    if sys.platform != "darwin":
        return False
    try:
        subprocess.run(
            [
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera",
            ],
            check=False,
            timeout=5,
        )
        return True
    except Exception:
        return False


def camera_access_message(status: CameraPermission | None = None) -> str:
    status = status if status is not None else camera_permission_status()
    if not is_eventra_app_bundle():
        return (
            "Camera access needs the EVENTRA app. Close this window and start "
            "EVENTRA again with ./run.sh, then allow camera access when macOS asks."
        )
    if status is CameraPermission.DENIED:
        return (
            "Camera access is blocked. Open System Settings > Privacy & Security > "
            "Camera, enable EVENTRA, then restart the app."
        )
    if status is CameraPermission.RESTRICTED:
        return (
            "Camera access is restricted by this Mac's Screen Time or device "
            "management settings."
        )
    if status is CameraPermission.NOT_DETERMINED:
        return "Click Start Camera and choose Allow when macOS asks for camera access."
    if status is CameraPermission.UNKNOWN:
        return (
            "If the camera will not open, enable EVENTRA under System Settings > "
            "Privacy & Security > Camera, then restart the app."
        )
    return ""
