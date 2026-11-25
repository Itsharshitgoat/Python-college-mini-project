"""Design system: palette, typography and reusable styling helpers."""

from __future__ import annotations

import tkinter.font as tkfont

from config import APP_NAME

# Palette
NAVY = "#172554"
NAVY_LIGHT = "#1E3A8A"
SLATE = "#334155"
TEAL = "#14B8A6"
TEAL_DARK = "#0D9488"
BG = "#F5F7FA"
SURFACE = "#FFFFFF"
TEXT = "#1E293B"
MUTED = "#64748B"
BORDER = "#E2E8F0"
SUCCESS = "#16A34A"
SUCCESS_BG = "#ECFDF5"
WARNING = "#D97706"
WARNING_BG = "#FFFBEB"
ERROR = "#DC2626"
ERROR_BG = "#FEF2F2"
INFO_BG = "#EFF6FF"
NAVY_SOFT = "#E8EDF7"

FONT_PREFERENCES = ("Inter", "Aptos", "Segoe UI", "SF Pro Text", "Arial", "Helvetica")


def _detect_font() -> str:
    try:
        available = set(tkfont.families())
    except Exception:
        return "Arial"
    for family in FONT_PREFERENCES:
        if family in available:
            return family
    return "Arial"


FONT_FAMILY = _detect_font()


def font(size: int = 13, weight: str = "normal"):
    return (FONT_FAMILY, size, weight)


def heading(size: int = 26):
    return font(size, "bold")


def subheading(size: int = 18):
    return font(size, "bold")


def body(size: int = 13):
    return font(size)


def small(size: int = 11):
    return font(size)


def button_style(kind: str = "primary") -> dict:
    """Return CTkButton keyword arguments for a semantic action colour."""
    styles = {
        "primary": {"fg_color": TEAL, "hover_color": TEAL_DARK, "text_color": "white"},
        "secondary": {
            "fg_color": NAVY, "hover_color": NAVY_LIGHT, "text_color": "white"
        },
        "outline": {
            "fg_color": SURFACE,
            "hover_color": BORDER,
            "text_color": TEXT,
            "border_width": 1,
            "border_color": BORDER,
        },
        "danger": {"fg_color": ERROR, "hover_color": "#B91C1C", "text_color": "white"},
        "ghost": {
            "fg_color": "transparent",
            "hover_color": NAVY_SOFT,
            "text_color": "#C7D2FE",
        },
    }
    return styles.get(kind, styles["primary"])


def card_style() -> dict:
    return {
        "fg_color": SURFACE,
        "corner_radius": 14,
        "border_width": 1,
        "border_color": BORDER,
    }


def window_title(section: str) -> str:
    return f"{APP_NAME}  |  {section}" if section else APP_NAME
