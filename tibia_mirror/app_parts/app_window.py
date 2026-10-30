"""The main window of the app."""

from __future__ import annotations

import tkinter as tk
from types import TracebackType

from tibia_mirror import errors
from tibia_mirror.config import (
    APP_ID,
    ICON_FILE,
    PANEL_FRAME,
    PANEL_MIN_SIZE,
    PANEL_SIZE,
    SHOW_REQUEST_POLL_MS,
)
from tibia_mirror.core.geometry import fit_panel_size, panel_geometry
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.base import scale, theme
from tibia_mirror.winapi import dwm, win32
from tibia_mirror.winapi.instance import SingleInstance


class AppWindow(tk.Tk):
    """The main window of the app."""

    def __init__(self, settings: AppSettingsStore, instance: SingleInstance) -> None:
        self._settings = settings
        self._instance = instance  # tells when a second start of the app asks for this window
        self._prepare_windows()
        super().__init__()
        self.withdraw()  # hidden until show() is called
        # the number Windows knows this window by
        self._window_handle: Hwnd = win32.toplevel_hwnd(self)
        self.title("Tibia Mirror")
        self._use_display_scaling()
        self._set_theme()
        self._set_icon()
        self._set_size_and_place()
        self.set_panel_on_top()
        self._bind_events()
        self._check_show_request()

    def report_callback_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        """Write an error from a click, a key or a timer to the error log.

        Tk calls this method itself when such an error happens.
        """
        errors.log_exception(exc_type, exc_value, exc_traceback)

    def show(self) -> None:
        """Show the window. It stays hidden until the app calls this."""
        self.deiconify()

    def set_panel_on_top(self) -> None:
        """Keep the window above other windows, or not, as the setting says."""
        self.attributes("-topmost", self._settings.current.is_panel_on_top)

    def _set_theme(self) -> None:
        """Load the saved theme and give the window its colours."""
        # Button styles contain pixel sizes, so the theme is loaded after the scaling.
        theme.use(self._settings.current.theme)
        self.configure(bg=theme.BG)
        self._style_title_bar()

    def _prepare_windows(self) -> None:
        """Keep the app sharp on scaled displays and give it its own taskbar button.

        Windows needs both before the first window is created.
        """
        win32.enable_dpi_awareness()
        win32.set_app_id(APP_ID)

    def _use_display_scaling(self) -> None:
        """Make our pixel sizes grow with the display scaling (125%, 150%, ...)."""
        scale.init(self)

    def _set_icon(self) -> None:
        """Use the app icon for this window and for every dialog."""
        # The same as self.iconbitmap(default=ICON_FILE).
        # mypy rejects that method (it has no type hints), so the command is sent as text.
        self.tk.call("wm", "iconbitmap", str(self), "-default", str(ICON_FILE))

    def _set_size_and_place(self) -> None:
        """Open where the window was the last time, or in the middle of the main screen.

        Sizes in config.py are for 100% scaling, so they are scaled here.
        On a smaller screen the window is made smaller to fit.
        """
        min_size = scale.px(PANEL_MIN_SIZE[0]), scale.px(PANEL_MIN_SIZE[1])
        title_bar = scale.px(PANEL_FRAME)
        saved_rect = self._settings.current.panel_rect
        self.minsize(*min_size)

        if saved_rect is None:
            size = scale.px(PANEL_SIZE[0]), scale.px(PANEL_SIZE[1])
            screen = win32.work_area_at((0, 0))
            self.geometry(panel_geometry(size, min_size[1], title_bar, screen))
            return

        position_x, position_y, width, height = saved_rect
        screen = win32.work_area_at((position_x + width // 2, position_y + height // 2))
        width, height = fit_panel_size((width, height), min_size, title_bar, screen)
        self.geometry(f"{width}x{height}+{position_x}+{position_y}")

    def _check_show_request(self) -> None:
        """Come to the front when a second start of the app asked for it."""
        # plan the next check first, so an error in this one cannot stop the checks
        self.after(SHOW_REQUEST_POLL_MS, self._check_show_request)

        if self._instance.show_requested():
            win32.bring_to_front(self._window_handle)

    def _style_title_bar(self) -> None:
        """Make the title bar dark in the dark theme. Windows draws it, so we ask Windows."""
        is_dark: bool = theme.current == "dark"

        dwm.set_dark_title_bar(self._window_handle, is_dark)

    def _bind_events(self) -> None:
        self.bind("<Configure>", self._on_place_changed, add="+")
        self.protocol("WM_DELETE_WINDOW", self._on_close)  # the X button and Alt+F4

    def _on_place_changed(self, event: tk.Event[tk.Misc]) -> None:
        # every widget inside the window sends its own <Configure> here too
        is_window_event = event.widget is self
        # minimized or maximized, the window opens at its normal place the next time
        is_normal = self.state() == "normal"

        if not is_window_event or not is_normal:
            return

        panel_rect = (self.winfo_x(), self.winfo_y(), event.width, event.height)
        self._settings.update(panel_rect=panel_rect)

    def _on_close(self) -> None:
        # a settings change from the last moment may still wait to be written
        try:
            self._settings.save()
        finally:
            self.destroy()
