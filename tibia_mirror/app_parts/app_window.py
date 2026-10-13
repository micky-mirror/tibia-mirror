"""The main window of the app."""

import tkinter as tk
from types import TracebackType

from tibia_mirror import errors
from tibia_mirror.config import APP_ID, ICON_FILE, PANEL_FRAME, PANEL_MIN_SIZE, PANEL_SIZE
from tibia_mirror.core.geometry import panel_geometry
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.base import scale, theme
from tibia_mirror.winapi import win32


class AppWindow(tk.Tk):
    """The main window of the app."""

    def __init__(self, settings: AppSettingsStore) -> None:
        self._settings = settings
        self._prepare_windows()
        super().__init__()
        self.withdraw()  # hidden until show() is called
        self.title("Tibia Mirror")
        self._use_display_scaling()
        self.use_saved_theme()
        self._set_icon()
        self._set_size_and_place()
        self.use_panel_on_top()

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

    def use_panel_on_top(self) -> None:
        """Keep the window above other windows, or not, as the setting says."""
        self.attributes("-topmost", self._settings.current.is_panel_on_top)

    def use_saved_theme(self) -> None:
        """Load the saved theme and give the window its background colour."""
        # Button styles contain pixel sizes, so the theme is loaded after the scaling.
        theme.use(self._settings.current.theme)
        self.configure(bg=theme.BG)

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
        """Open at the normal size, in the middle of the main screen.

        Sizes in config.py are for 100% scaling, so they are scaled here.
        On a short screen the window is made shorter to fit.
        """
        width, height = scale.px(PANEL_SIZE[0]), scale.px(PANEL_SIZE[1])
        min_width, min_height = scale.px(PANEL_MIN_SIZE[0]), scale.px(PANEL_MIN_SIZE[1])
        title_bar = scale.px(PANEL_FRAME)
        screen = win32.work_area_at((0, 0))
        self.minsize(min_width, min_height)
        self.geometry(panel_geometry((width, height), min_height, title_bar, screen))
