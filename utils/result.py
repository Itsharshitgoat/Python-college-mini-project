"""Standardized results returned by services and controllers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ResultCode:
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    DUPLICATE_REGISTRATION = "DUPLICATE_REGISTRATION"
    CAPACITY_REACHED = "CAPACITY_REACHED"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    INVALID_QR = "INVALID_QR"
    UNREGISTERED_QR = "UNREGISTERED_QR"
    CANCELLED = "CANCELLED"
    WRONG_EVENT = "WRONG_EVENT"
    EVENT_CLOSED = "EVENT_CLOSED"
    ALREADY_CHECKED_IN = "ALREADY_CHECKED_IN"
    EXPIRED = "EXPIRED"
    CAMERA_ERROR = "CAMERA_ERROR"


@dataclass
class Result:
    success: bool
    code: str
    message: str
    data: Any = None

    @classmethod
    def ok(cls, message: str = "", data: Any = None, code: str = ResultCode.SUCCESS) -> "Result":
        return cls(success=True, code=code, message=message, data=data)

    @classmethod
    def fail(cls, code: str, message: str, data: Any = None) -> "Result":
        return cls(success=False, code=code, message=message, data=data)

    @property
    def is_ok(self) -> bool:
        return self.success
