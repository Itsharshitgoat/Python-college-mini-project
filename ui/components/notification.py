"""Small transient toast notifications."""

from __future__ import annotations

import customtkinter as ctk

from ui.theme import ERROR, ERROR_BG, SUCCESS, SUCCESS_BG, WARNING, WARNING_BG, font

_KINDS = {
    "success": (SUCCESS, SUCCESS_BG, "✓"),
    "error": (ERROR, ERROR_BG, "✕"),
    "warning": (WARNING, WARNING_BG, "!"),
}


def notify(master, message: str, kind: str = "success", duration_ms: int = 3600) -> None:
    """Show a lightweight in-window toast without creating another top-level window."""
    accent, background, icon = _KINDS.get(kind, _KINDS["success"])
    host = master.winfo_toplevel()

    toast = ctk.CTkFrame(
        host, fg_color=background, corner_radius=12, border_width=1, border_color=accent
    )
    ctk.CTkLabel(
        toast, text=icon, font=font(18, "bold"), text_color=accent, width=28
    ).pack(side="left", padx=(16, 4), pady=14)
    ctk.CTkLabel(
        toast, text=message, font=font(12), text_color="#1E293B", wraplength=340,
        justify="left",
    ).pack(side="left", padx=(4, 18), pady=14)

    toast.place(relx=1.0, rely=1.0, x=-24, y=-24, anchor="se")
    toast.lift()
    toast.after(duration_ms, toast.destroy)
