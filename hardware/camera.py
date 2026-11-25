"""Webcam wrapper used by the scanner worker thread."""

from __future__ import annotations

from collections.abc import Iterable

import cv2
import numpy as np


class Camera:
    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        self.index = int(index)
        self.width = int(width)
        self.height = int(height)
        self._capture: cv2.VideoCapture | None = None

    @property
    def is_opened(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> bool:
        return self.open_indices([self.index]) is not None

    def open_indices(self, indices: Iterable[int]) -> int | None:
        """Open the first working camera and return its index."""
        backends = [getattr(cv2, "CAP_AVFOUNDATION", 0), 0]
        tried: list[int] = []
        for candidate in indices:
            try:
                index = int(candidate)
            except (TypeError, ValueError):
                continue
            if index < 0 or index in tried:
                continue
            tried.append(index)
            for backend in backends:
                capture = cv2.VideoCapture(index, backend)
                if capture.isOpened():
                    capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                    self._capture = capture
                    self.index = index
                    return index
                capture.release()
        return None

    def read(self) -> tuple[bool, np.ndarray | None]:
        if not self.is_opened:
            return False, None
        ok, frame = self._capture.read()
        return (True, frame) if ok and frame is not None else (False, None)

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
