"""Application bootstrap and lifecycle."""

from __future__ import annotations

from config import (
    APP_NAME,
    APP_TAGLINE,
    APP_VERSION,
    DEFAULT_WINDOW_SIZE,
    LOGIN_WINDOW_SIZE,
    MIN_WINDOW_SIZE,
    Paths,
)
from core.context import AppContext
from ui.components.scrolling import install_scroll_fixes
from ui.theme import window_title


class EventraApp:
    def __init__(self, paths: Paths | None = None):
        install_scroll_fixes()
        self.ctx = AppContext.create(paths)
        self._apply_theme()

        import customtkinter as ctk

        self.root = ctk.CTk()
        self.root.title(window_title("Sign In"))
        self.root.geometry(LOGIN_WINDOW_SIZE)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.main_window = None
        self.login_screen = None
        self._show_login()

    # --- theme ---------------------------------------------------------
    def _apply_theme(self) -> None:
        import customtkinter as ctk

        theme = self.ctx.settings_controller.get("theme", "Light")
        ctk.set_appearance_mode("Dark" if str(theme).lower() == "dark" else "Light")
        ctk.set_default_color_theme("blue")

    # --- screens -------------------------------------------------------
    def _clear_root(self) -> None:
        for child in list(self.root.winfo_children()):
            child.destroy()

    def _show_login(self) -> None:
        from ui.login import LoginScreen

        self._clear_root()
        self.root.title(window_title("Sign In"))
        self.root.geometry(LOGIN_WINDOW_SIZE)
        self.root.resizable(False, False)
        self.login_screen = LoginScreen(self.root, self.ctx, on_success=self._on_login)

    def _on_login(self, user) -> None:
        self.ctx.session.login(user)
        self._clear_root()
        self.root.title(window_title("Dashboard"))
        self.root.geometry(DEFAULT_WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)
        self.root.resizable(True, True)
        from ui.main_window import MainWindow

        self.main_window = MainWindow(self.root, self.ctx, self)

    def logout(self) -> None:
        if self.main_window:
            self.main_window.stop_camera()
        self.ctx.session.logout()
        self.main_window = None
        self.root.minsize(0, 0)
        self._show_login()

    def on_close(self) -> None:
        if self.main_window:
            self.main_window.stop_camera()
        self.ctx.shutdown()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def app_metadata() -> dict:
    return {"name": APP_NAME, "version": APP_VERSION, "tagline": APP_TAGLINE}
