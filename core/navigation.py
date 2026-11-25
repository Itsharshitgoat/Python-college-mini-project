"""Single-window screen switching with lightweight screen reuse."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from core.context import AppContext

# Context values that change a screen's behaviour but should not create a
# permanently cached copy of that screen.
_TRANSIENT_CONTEXT = frozenset({"open_dialog", "open_registration"})


class NavigationManager:
    def __init__(self, ctx: AppContext, content_frame: ctk.CTkFrame):
        self.ctx = ctx
        self.content = content_frame
        self.current_key: str | None = None
        self.current_context: dict[str, Any] = {}
        self.current_screen: ctk.CTkFrame | None = None
        self._screens: dict[tuple, ctk.CTkFrame] = {}
        self._dirty: set[tuple] = set()

    # --- cache helpers --------------------------------------------------
    @staticmethod
    def _cache_key(key: str, screen_context: dict[str, Any]) -> tuple:
        items = tuple(sorted(
            (name, value) for name, value in screen_context.items()
            if name not in _TRANSIENT_CONTEXT
            and not (key in ("scanner", "attendance") and name == "event_id")
        ))
        return (key, items)

    def mark_dirty(self, key: str, **screen_context) -> None:
        """Refresh a cached screen the next time it is shown."""
        self._dirty.add(self._cache_key(key, screen_context))

    def invalidate(self, key: str, **screen_context) -> None:
        cache_key = self._cache_key(key, screen_context)
        self._dirty.discard(cache_key)
        screen = self._screens.pop(cache_key, None)
        if screen is not None and screen is not self.current_screen:
            screen.destroy()

    # --- navigation -----------------------------------------------------
    def navigate(self, key: str, **screen_context) -> ctk.CTkFrame:
        cache_key = self._cache_key(key, screen_context)
        factory = self._factory(key)

        if self.current_screen is not None:
            if hasattr(self.current_screen, "stop_camera"):
                self.current_screen.stop_camera()

        for other_key, screen in self._screens.items():
            if other_key == cache_key:
                continue
            if screen is self.current_screen and hasattr(screen, "stop_camera"):
                screen.stop_camera()
            if screen.winfo_ismapped():
                screen.pack_forget()

        screen = self._screens.get(cache_key)
        is_new = screen is None
        if is_new:
            create_context = {
                name: value for name, value in screen_context.items()
                if name not in _TRANSIENT_CONTEXT
            }
            screen = factory(master=self.content, ctx=self.ctx, nav=self, **create_context)
            self._screens[cache_key] = screen
            screen.pack(fill="both", expand=True)
        else:
            screen.pack(fill="both", expand=True)

        self.current_key = key
        self.current_context = dict(screen_context)
        self.current_screen = screen

        if not is_new and "event_id" in screen_context and hasattr(screen, "initial_event_id"):
            screen.initial_event_id = screen_context["event_id"]
            if hasattr(screen, "refresh"):
                screen.refresh()

        if is_new or cache_key in self._dirty:
            if hasattr(screen, "refresh"):
                screen.refresh()
            self._dirty.discard(cache_key)
        return screen

    def refresh(self) -> None:
        if self.current_key is None or self.current_screen is None:
            return
        cache_key = self._cache_key(self.current_key, self.current_context)
        self._dirty.discard(cache_key)
        if hasattr(self.current_screen, "refresh"):
            self.current_screen.refresh()

    def shutdown(self) -> None:
        for screen in self._screens.values():
            if hasattr(screen, "stop_camera"):
                screen.stop_camera()

    # --- factories ------------------------------------------------------
    def _factory(self, key: str):
        from ui.screens.attendance import AttendanceScreen
        from ui.screens.dashboard import DashboardScreen
        from ui.screens.event_details import EventDetailsScreen
        from ui.screens.events import EventsScreen
        from ui.screens.registration import RegistrationScreen
        from ui.screens.reports import ReportsScreen
        from ui.screens.scanner import ScannerScreen
        from ui.screens.settings import SettingsScreen
        from ui.screens.users import UsersScreen

        factories = {
            "dashboard": lambda **kw: DashboardScreen(**kw),
            "events": lambda **kw: EventsScreen(**kw),
            "event_details": lambda **kw: EventDetailsScreen(**kw),
            "registration": lambda **kw: RegistrationScreen(**kw),
            "scanner": lambda **kw: ScannerScreen(**kw),
            "attendance": lambda **kw: AttendanceScreen(**kw),
            "reports": lambda **kw: ReportsScreen(**kw),
            "users": lambda **kw: UsersScreen(**kw),
            "settings": lambda **kw: SettingsScreen(**kw),
        }
        if key not in factories:
            raise ValueError(f"Unknown screen: {key}")
        return factories[key]
