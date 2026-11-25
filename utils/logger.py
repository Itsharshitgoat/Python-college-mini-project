"""Application logging setup."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_CONFIGURED = False


def configure_logger(log_dir: Path) -> logging.Logger:
    global _CONFIGURED
    logger = logging.getLogger("eventra")
    if _CONFIGURED:
        return logger

    log_dir.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    file_handler = RotatingFileHandler(
        log_dir / "application.log", maxBytes=2_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    _CONFIGURED = True
    return logger


def get_logger(name: str = "eventra") -> logging.Logger:
    return logging.getLogger(name)
