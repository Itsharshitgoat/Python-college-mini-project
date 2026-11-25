"""Small UI helpers."""

from __future__ import annotations

from typing import Callable


def debounced(master, callback: Callable[[], None], delay_ms: int = 250) -> Callable[..., None]:
    """Return a trace/command callback that runs ``callback`` after typing stops."""
    after_id: str | None = None

    def run() -> None:
        nonlocal after_id
        after_id = None
        callback()

    def schedule(*_args) -> None:
        nonlocal after_id
        if after_id is not None:
            try:
                master.after_cancel(after_id)
            except Exception:
                pass
        after_id = master.after(delay_ms, run)

    return schedule
