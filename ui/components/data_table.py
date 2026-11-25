"""Fast, structured table built on Tk's native Treeview."""

from __future__ import annotations

from tkinter import ttk
from typing import Callable, Sequence

import customtkinter as ctk

from ui.theme import BORDER, MUTED, SURFACE, TEXT, card_style, font

_STYLE_READY = False


def _ensure_style(master) -> None:
    """Configure a consistent native table style once per process."""
    global _STYLE_READY
    if _STYLE_READY:
        return
    style = ttk.Style(master)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(
        "Eventra.Treeview",
        background=SURFACE,
        fieldbackground=SURFACE,
        foreground=TEXT,
        rowheight=36,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        font=font(12),
    )
    style.configure(
        "Eventra.Treeview.Heading",
        background="#F8FAFC",
        foreground=MUTED,
        font=font(11, "bold"),
        bordercolor=BORDER,
        relief="flat",
    )
    style.map(
        "Eventra.Treeview",
        background=[("selected", "#DDF4F0")],
        foreground=[("selected", TEXT)],
    )
    style.configure(
        "Eventra.Vertical.TScrollbar",
        background="#CBD5E1",
        troughcolor=SURFACE,
        bordercolor=SURFACE,
        arrowcolor=MUTED,
        relief="flat",
    )
    _STYLE_READY = True


class DataTable(ctk.CTkFrame):
    """
    columns: Sequence[(header_label, weight)]
    rows:    Sequence[Sequence[str]]  (display strings)
    """

    def __init__(
        self,
        master,
        columns: Sequence[tuple[str, int]],
        rows: Sequence[Sequence] = (),
        on_select: Callable[[int], None] | None = None,
        on_double_click: Callable[[int], None] | None = None,
        empty_text: str = "No records found.",
        **kwargs,
    ):
        super().__init__(master, **card_style(), **kwargs)
        _ensure_style(master)
        self.columns = list(columns)
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.empty_text = empty_text
        self.selected_index: int | None = None
        self._rows: list[tuple[str, ...]] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.column_ids = [f"col{index}" for index in range(len(self.columns))]
        self.tree = ttk.Treeview(
            self,
            columns=self.column_ids,
            show="headings",
            selectmode="browse",
            style="Eventra.Treeview",
        )
        self.tree.tag_configure("oddrow", background="#F8FAFC")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)

        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.tree.yview,
            style="Eventra.Vertical.TScrollbar",
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=8)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        total_weight = max(sum(weight for _, weight in self.columns), 1)
        for column_id, (label, weight) in zip(self.column_ids, self.columns):
            width = max(86, int(980 * weight / total_weight))
            self.tree.heading(column_id, text=label.upper(), anchor="w")
            self.tree.column(
                column_id, width=width, minwidth=72, anchor="w", stretch=True
            )

        self.empty_label = ctk.CTkLabel(
            self, text=empty_text, font=font(13), text_color=MUTED, anchor="center"
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        if on_double_click:
            self.tree.bind("<Double-1>", self._on_double_click)

        self.set_rows(rows)

    def set_rows(self, rows: Sequence[Sequence]) -> None:
        self._rows = [
            tuple(str(value) if value not in (None, "") else "-" for value in row)
            for row in rows
        ]
        self.tree.delete(*self.tree.get_children())
        self.selected_index = None

        if not self._rows:
            self.empty_label.configure(text=self.empty_text)
            self.empty_label.place(relx=0.5, rely=0.5, anchor="center")
            return

        self.empty_label.place_forget()
        for index, values in enumerate(self._rows):
            self.tree.insert(
                "", "end", iid=str(index), values=values,
                tags=("oddrow",) if index % 2 else (),
            )

    def select(self, index: int) -> None:
        if 0 <= index < len(self._rows):
            self.tree.selection_set(str(index))
            self.tree.focus(str(index))
            self.tree.see(str(index))
            self.selected_index = index

    def clear_selection(self) -> None:
        self.tree.selection_remove(*self.tree.selection())
        self.tree.focus("")
        self.selected_index = None

    def _on_select(self, _event=None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        try:
            index = int(selection[0])
        except ValueError:
            return
        self.selected_index = index
        if self.on_select:
            self.on_select(index)

    def _on_double_click(self, event) -> None:
        row = self.tree.identify_row(event.y)
        if not row or not self.on_double_click:
            return
        try:
            index = int(row)
        except ValueError:
            return
        self.select(index)
        self.on_double_click(index)
