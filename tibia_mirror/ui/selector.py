"""Full-monitor translucent overlay for dragging out a new region."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.config import MIN_SELECTION_SIDE
from tibia_mirror.core.geometry import Point, Rect, nudged_point, overlay_to_client, rect_from_drag
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.ui import theme
from tibia_mirror.ui.loupe import Loupe
from tibia_mirror.ui.scale import px
from tibia_mirror.winapi import win32

# Arrow keys shift the selection's point this many pixels (with Shift, NUDGE_SHIFT times).
NUDGE = {"Left": (-1, 0), "Right": (1, 0), "Up": (0, -1), "Down": (0, 1)}
NUDGE_SHIFT = 10
OUTLINE = 2  # the selection's outline, at 100% display scaling


class RegionSelector:
    """Covers the game's monitor; on release calls on_done(rect in client coordinates).

    Escape or a tiny drag calls on_cancel(). Arrow keys shift the selected point by
    a pixel (Shift: 10) without moving the mouse pointer; the Loupe shows it.
    """

    def __init__(
        self,
        root: tk.Misc,
        game_hwnd: Hwnd,
        on_done: Callable[[Rect], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.game_hwnd = game_hwnd
        self.on_done = on_done
        self.on_cancel = on_cancel
        monitor = win32.monitor_rect(game_hwnd)
        self.monitor_origin = (monitor.x, monitor.y)

        self.overlay = tk.Toplevel(root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.3)
        self.overlay.configure(bg="black", cursor="crosshair")
        self.overlay.geometry(f"{monitor.w}x{monitor.h}+{monitor.x}+{monitor.y}")

        self.canvas = tk.Canvas(self.overlay, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.box: int | None = None
        self.start_x = self.start_y = 0
        self._nudge: Point = (0, 0)  # added to the pointer's position, in pixels
        # The pointer's last position on the overlay, as its events report it.
        pointer_x, pointer_y = win32.cursor_pos()
        self._pointer: Point = (pointer_x - monitor.x, pointer_y - monitor.y)
        self._size = (monitor.w, monitor.h)
        self.canvas.bind("<Button-1>", self._start)
        self.canvas.bind("<B1-Motion>", self._move)
        self.canvas.bind("<ButtonRelease-1>", self._end)
        self.overlay.bind("<Escape>", lambda e: self.cancel())
        self.overlay.protocol("WM_DELETE_WINDOW", self.cancel)  # e.g. Alt+F4
        for key, (dx, dy) in NUDGE.items():
            self.overlay.bind(f"<{key}>", self._nudger(dx, dy))
            self.overlay.bind(f"<Shift-{key}>", self._nudger(dx * NUDGE_SHIFT, dy * NUDGE_SHIFT))
        self.canvas.bind("<Motion>", self._hover)
        self.loupe = Loupe(root, game_hwnd, win32.client_rect(game_hwnd))
        self._show()
        self.overlay.focus_force()

    def _nudger(self, dx: int, dy: int) -> Callable[[tk.Event[tk.Misc]], None]:
        """An arrow key's binding: shift the selection's point by (dx, dy) pixels."""

        def nudge(_e: tk.Event[tk.Misc]) -> None:
            nudge_x, nudge_y = self._nudge
            self._nudge = (nudge_x + dx, nudge_y + dy)
            self._show()

        return nudge

    def _point(self) -> Point:
        """Where the selection is taken from: the pointer plus the nudge, on the overlay."""
        return nudged_point(self._pointer, self._nudge, *self._size)

    def _show(self) -> None:
        """Draw the selection up to the point, and aim the Loupe at it."""
        x, y = self._point()
        origin_x, origin_y = self.monitor_origin
        if self.box is None:
            self.loupe.update(origin_x + x, origin_y + y)
            return
        self.canvas.coords(self.box, self.start_x, self.start_y, x, y)
        selection = rect_from_drag(self.start_x, self.start_y, x, y)
        self.loupe.update(origin_x + x, origin_y + y, (selection.w, selection.h))

    def _hover(self, e: tk.Event[tk.Canvas]) -> None:
        self._pointer = (e.x, e.y)
        self._show()

    def _start(self, e: tk.Event[tk.Canvas]) -> None:
        self._pointer = (e.x, e.y)
        self.start_x, self.start_y = self._point()
        self.box = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline=theme.ACCENT,
            width=px(OUTLINE),
        )

    def _move(self, e: tk.Event[tk.Canvas]) -> None:
        if self.box is None:
            return  # a drag that did not start on the overlay
        self._pointer = (e.x, e.y)
        self._show()

    def _close(self) -> None:
        self.loupe.destroy()
        self.overlay.destroy()

    def _end(self, e: tk.Event[tk.Canvas]) -> None:
        self._close()
        self._pointer = (e.x, e.y)
        selection = rect_from_drag(self.start_x, self.start_y, *self._point())
        if selection.w < MIN_SELECTION_SIDE or selection.h < MIN_SELECTION_SIDE:
            self.on_cancel()
            return
        self.on_done(
            overlay_to_client(selection, self.monitor_origin, win32.client_origin(self.game_hwnd))
        )

    def cancel(self) -> None:
        self._close()
        self.on_cancel()
