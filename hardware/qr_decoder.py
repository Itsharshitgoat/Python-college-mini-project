"""OpenCV-based QR detection and decoding."""

from __future__ import annotations

import cv2
import numpy as np


class QrDecoder:
    def __init__(self):
        self.detector = cv2.QRCodeDetector()

    def decode(self, frame: np.ndarray) -> tuple[str | None, np.ndarray | None]:
        """Return (payload, corner points) or (None, None)."""
        try:
            data, points, _ = self.detector.detectAndDecode(frame)
        except cv2.error:
            return None, None
        if not data:
            return None, None
        return data, points

    @staticmethod
    def draw_marker(frame: np.ndarray, points: np.ndarray | None) -> np.ndarray:
        if points is None:
            return frame
        try:
            pts = points.reshape((-1, 1, 2)).astype(int)
            cv2.polylines(frame, [pts], True, (20, 184, 166), 3)
        except (cv2.error, ValueError):
            pass
        return frame
