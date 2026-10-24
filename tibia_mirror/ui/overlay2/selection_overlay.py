"""The dark cover where the user drags a box over a part of the game."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.config import MIN_SELECTION_SIDE
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Point, Rect, overlay_to_client, rect_from_drag
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.winapi import win32

COVER_OPACITY = 0.3  # how much the cover darkens the screen under it
# Sizes at 100% display scaling; px() scales them where they are used.
BOX_OUTLINE = 2  # the line around the selected box


class SelectionOverlay(tk.Toplevel):
    """A dark cover over the monitor of the game, for selecting a part of the game."""

    def __init__(
        self,
        parent: tk.Misc,
        game_window: GameWindow,
        on_selected: Callable[[Rect], None],
    ) -> None:
        super().__init__(parent)
        self._game_window = game_window
        self._on_selected = on_selected  # gets the selected part, in game coordinates
        self._monitor_area = win32.monitor_rect(game_window.handle)  # on the screen
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above other windows, also above the game
        # window layer setup
        self.attributes("-alpha", COVER_OPACITY)
        self.configure(bg="black", cursor="crosshair")
        # render window over the whole monitor of the game
        self._cover_monitor()
        # the surface the box is drawn on
        self._add_canvas()
        self._box: int | None = None  # the box on the canvas, None until the mouse is pressed
        self._start_point: Point = (0, 0)  # where the drag started, on the cover
        # take the keys at once, so Escape works without a click first
        self.focus_force()
        self._bind_events()

    def _cover_monitor(self) -> None:
        monitor = self._monitor_area
        self.geometry(f"{monitor.w}x{monitor.h}+{monitor.x}+{monitor.y}")

    def _add_canvas(self) -> None:
        self._canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self._canvas.pack(fill="both", expand=True)

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.protocol("WM_DELETE_WINDOW", self.destroy)  # Alt+F4
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self.destroy()

    def _on_mouse_down(self, event: tk.Event[tk.Misc]) -> None:
        self._start_point = (event.x, event.y)
        self._box = self._canvas.create_rectangle(
            *self._start_point,
            *self._start_point,
            outline=theme.ACCENT,
            width=px(BOX_OUTLINE),
        )

    def _on_mouse_drag(self, event: tk.Event[tk.Misc]) -> None:
        if self._box is None:
            return  # the drag started before the cover opened

        self._canvas.coords(self._box, *self._start_point, event.x, event.y)

    def _on_mouse_up(self, event: tk.Event[tk.Misc]) -> None:
        if self._box is None:
            return  # the press was before the cover opened

        self.destroy()
        selection = rect_from_drag(*self._start_point, event.x, event.y)
        is_click = selection.w < MIN_SELECTION_SIDE or selection.h < MIN_SELECTION_SIDE

        if is_click:
            return

        self._on_selected(self._get_game_area(selection))

    def _get_game_area(self, selection: Rect) -> Rect:
        monitor_origin = self._monitor_area.x, self._monitor_area.y
        client_origin = self._game_window.client_area.x, self._game_window.client_area.y
        return overlay_to_client(selection, monitor_origin, client_origin)
