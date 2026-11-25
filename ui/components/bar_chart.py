"""Lightweight native bar charts for analytics screens."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from ui.theme import BORDER, MUTED, SURFACE, TEXT, card_style, font

DEFAULT_COLORS = ("#14B8A6", "#D97706", "#172554", "#2563EB", "#7C3AED")


class BarChart(ctk.CTkFrame):
    """A small, fast bar chart drawn directly on a Tk canvas."""

    def __init__(self, master, title: str, **kwargs):
        super().__init__(master, **card_style(), **kwargs)
        self._values: list[tuple[str, float]] = []
        self._colors: list[str] = []
        self._last_size = (0, 0)

        ctk.CTkLabel(
            self, text=title, font=font(11, "bold"), text_color=MUTED, anchor="w"
        ).pack(anchor="w", padx=16, pady=(12, 4))

        self.canvas = tk.Canvas(
            self, bg=SURFACE, highlightthickness=0, bd=0, height=210
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 12))
        self.canvas.bind("<Configure>", self._on_configure)

    def set_values(self, values, colors=None) -> None:
        self._values = [
            (str(label), float(value)) for label, value in values
        ]
        self._colors = list(colors or DEFAULT_COLORS)
        self._draw()

    def _on_configure(self, event) -> None:
        size = (event.width, event.height)
        if size != self._last_size and event.width > 120 and event.height > 80:
            self._last_size = size
            self.after_idle(self._draw)

    def _draw(self, no_color_updates: bool = False, **_kwargs) -> None:
        # CTkFrame calls _draw() during construction with its own internal
        # keyword, so keep this override compatible and delegate rendering.
        self._render()

    def _render(self) -> None:
        if not hasattr(self, "canvas"):
            return
        canvas = self.canvas
        canvas.delete("all")
        width = canvas.winfo_width() or 440
        height = canvas.winfo_height() or 210
        if width < 120 or height < 80:
            return

        if not self._values:
            canvas.create_text(
                width / 2, height / 2, text="No data yet",
                font=font(12), fill=MUTED,
            )
            return

        left, right, top, bottom = 42, 16, 16, 38
        plot_height = max(height - top - bottom, 10)
        plot_width = max(width - left - right, 10)
        maximum = max(value for _, value in self._values) or 1

        for step in (0, 0.5, 1):
            y = top + plot_height - step * plot_height
            canvas.create_line(left, y, left + plot_width, y, fill=BORDER)
            canvas.create_text(
                left - 8, y, text=str(int(maximum * step)),
                font=font(9), fill=MUTED, anchor="e",
            )

        slot = plot_width / len(self._values)
        bar_width = max(16, min(58, slot * 0.55))
        baseline = top + plot_height

        for index, (label, value) in enumerate(self._values):
            color = self._colors[index % len(self._colors)] if self._colors else DEFAULT_COLORS[0]
            x_center = left + slot * index + slot / 2
            bar_height = max(2, (value / maximum) * plot_height)
            canvas.create_rectangle(
                x_center - bar_width / 2, baseline - bar_height,
                x_center + bar_width / 2, baseline,
                fill=color, outline="",
            )
            canvas.create_text(
                x_center, baseline - bar_height - 8, text=str(int(value)),
                font=font(9, "bold"), fill=TEXT,
            )
            short_label = label if len(label) <= 11 else label[:10] + "…"
            canvas.create_text(
                x_center, baseline + 18, text=short_label,
                font=font(9), fill=MUTED,
            )
