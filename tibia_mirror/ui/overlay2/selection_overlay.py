"""The dark cover where the user drags a box over a part of the game."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from tibia_mirror.config import MIN_SELECTION_SIDE
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import (
    Point,
    Rect,
    nudged_point,
    overlay_to_client,
    rect_from_drag,
)
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.overlay2.loupe import Loupe
from tibia_mirror.ui.panel.controls.name_dialog import NameDialog
from tibia_mirror.winapi import win32

COVER_OPACITY = 0.3  # how much the cover darkens the screen under it
# Sizes at 100% display scaling; px() scales them where they are used.
BOX_OUTLINE = 2  # the line around the selected box
# How far each arrow key moves the point of the box, in pixels.
NUDGE_STEPS = {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}


class SelectionOverlay(tk.Toplevel):
    """A dark cover over the monitor of the game, for selecting a part of the game."""

    def __init__(
        self,
        parent: tk.Misc,
        game_window: GameWindow,
        on_selected: Callable[[Rect], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self._game_window = game_window
        self._on_selected = on_selected  # gets the selected part, in game coordinates
        self._on_cancel = on_cancel  # called when the cover closes without a selection
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
        self._pointer: Point = self._get_pointer_on_cover()  # updated by each mouse event
        self._nudge: Point = (0, 0)  # how far the arrow keys moved the point from the pointer
        # the game under the point, bigger
        self._loupe = Loupe(self, game_window)
        self._show_point()
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
        self.protocol("WM_DELETE_WINDOW", self._cancel)  # Alt+F4
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<Motion>", self._on_mouse_move)  # with the mouse button held down too
        self.bind("<ButtonRelease-1>", self._on_mouse_up)
        for key in NUDGE_STEPS:
            self.bind(f"<KeyPress-{key}>", self._on_arrow_key)

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self._cancel()

    def _on_mouse_down(self, event: tk.Event[tk.Misc]) -> None:
        self._pointer = (event.x, event.y)
        self._start_point = self._get_point()
        self._box = self._canvas.create_rectangle(
            *self._start_point,
            *self._start_point,
            outline=theme.ACCENT,
            width=px(BOX_OUTLINE),
        )

    def _on_mouse_move(self, event: tk.Event[tk.Misc]) -> None:
        self._pointer = (event.x, event.y)
        self._show_point()

    def _on_mouse_up(self, event: tk.Event[tk.Misc]) -> None:
        if self._box is None:
            return  # the press was before the cover opened

        self._pointer = (event.x, event.y)
        selection = rect_from_drag(*self._start_point, *self._get_point())
        is_click = selection.w < MIN_SELECTION_SIDE or selection.h < MIN_SELECTION_SIDE

        if is_click:
            self._cancel()
            return

        self.destroy()
        self._on_selected(self._get_game_area(selection))

    def _on_arrow_key(self, event: tk.Event[tk.Misc]) -> None:
        step_x, step_y = NUDGE_STEPS[event.keysym]
        nudge_x, nudge_y = self._nudge

        self._nudge = (nudge_x + step_x, nudge_y + step_y)
        self._show_point()

    def _show_point(self) -> None:
        """Show the point in the loupe, and stretch the box to it."""
        point_x, point_y = self._get_point()
        monitor = self._monitor_area
        point_on_screen = (monitor.x + point_x, monitor.y + point_y)

        if self._box is None:
            self._loupe.show_at(point_on_screen)
            return  # no box until the mouse is pressed on the cover

        selection = rect_from_drag(*self._start_point, point_x, point_y)
        self._canvas.coords(self._box, *self._start_point, point_x, point_y)
        self._loupe.show_at(point_on_screen, (selection.w, selection.h))

    def _get_pointer_on_cover(self) -> Point:
        pointer_x, pointer_y = win32.cursor_pos()
        return pointer_x - self._monitor_area.x, pointer_y - self._monitor_area.y

    def _get_point(self) -> Point:
        """The pointer, moved by the arrow keys, and kept on the cover."""
        monitor = self._monitor_area
        return nudged_point(self._pointer, self._nudge, monitor.w, monitor.h)

    def _cancel(self) -> None:
        """Close the cover without a selection."""
        self.destroy()
        self._on_cancel()

    def _get_game_area(self, selection: Rect) -> Rect:
        monitor_origin = self._monitor_area.x, self._monitor_area.y
        client_origin = self._game_window.client_area.x, self._game_window.client_area.y
        return overlay_to_client(selection, monitor_origin, client_origin)


class NewRegionOverlay(SelectionOverlay):
    """The cover for a new mirror: it also asks for the name of the selected part."""

    def __init__(
        self,
        parent: tk.Misc,
        game_window: GameWindow,
        suggested_name: str,
        on_named: Callable[[Rect, str], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(parent, game_window, self._ask_name, on_cancel)
        self._parent = parent
        self._suggested_name = suggested_name  # what the name field starts with
        self._on_named = on_named  # gets the selected part, in game coordinates, and its name

    def _ask_name(self, area: Rect) -> None:
        NameDialog(
            self._parent,
            tr("Name this region"),
            self._suggested_name,
            on_ok=partial(self._on_named, area),
            on_cancel=self._on_cancel,
        )
