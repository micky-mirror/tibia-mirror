"""The main window of the app."""

import tkinter as tk
from types import TracebackType

from tibia_mirror import errors
from tibia_mirror.config import APP_ID, ICON_FILE
from tibia_mirror.ui.base import scale
from tibia_mirror.winapi import win32


class AppWindow(tk.Tk):
    """The main window of the app."""

    def __init__(self) -> None:
        self._prepare_windows()
        super().__init__()
        self._use_display_scaling()
        self._set_icon()

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
