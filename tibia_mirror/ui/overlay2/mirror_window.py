"""One mirror on the screen."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.config import COLOR_BORDER, FRAME_COLORS, MIRROR_BORDER, RESIZE_GRIP
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Rect, scaled_size
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.core.mirror_look import MirrorLook
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.regions import Layout, size_key
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.ui.overlay2.mirror_frame import MirrorFrame
from tibia_mirror.winapi import dwm, win32
from tibia_mirror.winapi.dwm import Thumbnail


class MirrorWindow(tk.Toplevel):
    """A window that shows a part of the game."""

    def __init__(
        self,
        parent: tk.Misc,
        mirror_settings: MirrorSettings,
        game_window: GameWindow,
        mirror_look: MirrorLook,
        on_changed: Callable[[MirrorSettings], None],
    ) -> None:
        super().__init__(parent)
        self.withdraw()  # hidden until it has a size and a place
        self._mirror_settings = mirror_settings
        self._game_window = game_window
        self._mirror_look = mirror_look
        self._on_changed = on_changed
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        # only the app closes a mirror
        keep_open(self)
        # the number Windows knows this window by
        self._window_handle: Hwnd = win32.toplevel_hwnd(self)
        # window layer setup
        win32.set_alpha(self._window_handle, mirror_settings.opacity)
        win32.set_click_through(self._window_handle, mirror_settings.is_locked)
        # the frame behind a rounded picture
        self._mirror_frame = MirrorFrame(self, mirror_settings.opacity)
        # initialize thumbnail connection
        self._thumbnail = self._create_thumbnail()
        # render window at given place
        self._show_at_saved_place()
        # react to the mouse
        self._grab_distance = (0, 0)
        self._bind_events()

    def destroy(self) -> None:
        """Stop the thumbnail and close the window."""
        self._thumbnail.close()
        super().destroy()

    def set_game_window(self, game_window: GameWindow) -> None:
        """Follow the window of Tibia after it changed."""
        self._game_window = game_window
        self._show_at_saved_place()

    def set_mirror_look(self, mirror_look: MirrorLook) -> None:
        """Draw the window with a new look."""
        self._mirror_look = mirror_look
        self._show_at_saved_place()

    def _bind_events(self) -> None:
        # <Enter> too: the pointer can come in and stop, with no <Motion> after it.
        self.bind("<Enter>", self._on_mouse_move)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_mouse_move(self, event: tk.Event[tk.Misc]) -> None:
        """Show the resize cursor over the bottom-right corner."""
        cursor = "size_nw_se" if self._is_in_resize_grip(event) else ""
        self.configure(cursor=cursor)

    def _on_mouse_down(self, event: tk.Event[tk.Misc]) -> None:
        """Keep how far the mouse is from the saved place of the mirror."""
        layout = self._get_layout()

        if layout is None:
            return

        offset_x, offset_y = layout.offset
        self._grab_distance = (event.x_root - offset_x, event.y_root - offset_y)

    def _on_mouse_drag(self, event: tk.Event[tk.Misc]) -> None:
        """Move the mirror with the mouse, and keep its new place."""
        layout = self._get_layout()

        if layout is None:
            return

        grab_x, grab_y = self._grab_distance
        new_offset = (event.x_root - grab_x, event.y_root - grab_y)
        self._set_layout(replace(layout, offset=new_offset))
        self._show_at_saved_place()

    def _on_mouse_up(self, event: tk.Event[tk.Misc]) -> None:
        """Hand over the settings of the mirror with its new place."""
        self._on_changed(self._mirror_settings)

    def _is_in_resize_grip(self, event: tk.Event[tk.Misc]) -> bool:
        """Whether the mouse is on the bottom-right corner, where the mirror is resized."""
        grip = px(RESIZE_GRIP)
        is_on_right_edge = event.x >= self.winfo_width() - grip
        is_on_bottom_edge = event.y >= self.winfo_height() - grip

        return is_on_right_edge and is_on_bottom_edge

    def _show_at_saved_place(self) -> None:
        """Show the window at its saved place, or hide it when it must not be shown."""
        layout = self._get_layout()
        is_tibia_in_use = self._game_window.is_in_front and not self._game_window.is_minimized

        if layout is None or self._mirror_settings.is_hidden or not is_tibia_in_use:
            self._mirror_frame.withdraw()
            self.withdraw()
            return

        picture_area = self._get_picture_area(layout)
        border = self._get_border_width()
        has_frame_window = self._has_frame_window()
        window_margin = 0 if has_frame_window else border

        window_area = picture_area.grown(window_margin)
        thumbnail_area = Rect(window_margin, window_margin, picture_area.w, picture_area.h)

        dwm.set_rounded_corners(self._window_handle, self._mirror_look.is_rounded_on)
        # first, so the picture ends up above its frame
        self._show_frame_window(picture_area, border)
        # shows as the frame around the picture
        self.configure(bg=theme.frame_color(self._mirror_settings.colour))
        self.geometry(f"{window_area.w}x{window_area.h}+{window_area.x}+{window_area.y}")
        self._thumbnail.show(layout.region, thumbnail_area)
        self.deiconify()
        self.attributes("-topmost", True)  # above other windows, also above the game

    def _get_picture_area(self, layout: Layout) -> Rect:
        """Where the picture of the game goes on the screen."""
        client_area = self._game_window.client_area
        zoom = self._mirror_settings.zoom
        area_width, area_height = scaled_size(layout.region.w, layout.region.h, zoom)
        position_x = client_area.x + layout.offset[0]
        position_y = client_area.y + layout.offset[1]

        return Rect(position_x, position_y, area_width, area_height)

    def _get_border_width(self) -> int:
        """The width of the frame around the picture."""
        if self._is_coloured():
            return px(COLOR_BORDER)

        if self._mirror_look.is_frame_on:
            return px(MIRROR_BORDER)

        return 0

    def _show_frame_window(self, picture_area: Rect, border: int) -> None:
        """Show the frame window around a rounded or tinted picture, or hide it."""
        is_frame_window_used = self._has_frame_window() and border > 0

        if not is_frame_window_used:
            self._mirror_frame.withdraw()
            return

        self._mirror_frame.show(
            picture_area,
            border,
            self._mirror_settings.colour,
            is_rounded=self._mirror_look.is_rounded_on,
            is_solid=self._is_tinted(),
        )

    def _has_frame_window(self) -> bool:
        """Whether the frame is drawn by the frame window, not by this window."""
        return self._mirror_look.is_rounded_on or self._is_tinted()

    def _is_tinted(self) -> bool:
        """Whether the picture is shaded in the frame colour."""
        return self._mirror_look.is_tint_on and self._is_coloured()

    def _is_coloured(self) -> bool:
        """Whether the mirror has a frame colour of its own."""
        return self._mirror_settings.colour != FRAME_COLORS[0]

    def _get_layout(self) -> Layout | None:
        """The saved layout for this size of the game. None if there is none."""
        return self._mirror_settings.layouts.get(self._get_size_key())

    def _set_layout(self, layout: Layout) -> None:
        """Keep a new layout for this size of the game."""
        layouts = {**self._mirror_settings.layouts, self._get_size_key(): layout}
        self._mirror_settings = replace(self._mirror_settings, layouts=layouts)

    def _get_size_key(self) -> str:
        """The size of the game as the key of its layout, for example "1920x1080"."""
        client_area = self._game_window.client_area

        return size_key(client_area.w, client_area.h)

    def _create_thumbnail(self) -> Thumbnail:
        """Ask Windows to draw a live copy of the game into this window.

        If Windows refuses, the window is closed and this raises OSError.
        """
        try:
            return Thumbnail(self._window_handle, self._game_window.handle)
        except OSError:
            super().destroy()
            raise
