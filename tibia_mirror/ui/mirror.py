"""One mirror: a borderless, always-on-top window showing a live DWM copy of part of Tibia."""

from __future__ import annotations

import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from tibia_mirror import dwm, win32
from tibia_mirror.config import (
    COLOR_BORDER,
    FRAME_COLORS,
    HIGHLIGHT_BORDER,
    MIRROR_BORDER,
    RESIZE_GRIP,
    ROUND_SMALL_RADIUS,
    ZOOM_RANGE,
)
from tibia_mirror.core.geometry import (
    Rect,
    clamp_box,
    resize_around_center,
    scaled_size,
    zoom_for_width,
)
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.core.regions import (
    Layout,
    SavedRegion,
    clamp_opacity,
    clamp_zoom,
    guess_layout,
    new_id,
    size_key,
)
from tibia_mirror.core.timers import TimerSettings, badge_text, is_done
from tibia_mirror.dwm import Thumbnail
from tibia_mirror.i18n import tr
from tibia_mirror.ui import theme
from tibia_mirror.ui.animation import Tween
from tibia_mirror.ui.badge import TimerBadge
from tibia_mirror.ui.scale import px
from tibia_mirror.ui.windows import keep_open


@dataclass(frozen=True)
class MirrorLook:
    """How every mirror is drawn, from the settings."""

    frame: bool  # thin MIRROR_BORDER frame when not highlighted
    fade_ms: int  # 0 switches fades off
    rounded: bool = False  # Windows 11's small rounded corners
    tint: bool = False  # mirrors with a frame colour are also shaded with it


class MirrorWindow:
    """One mirror: shows `saved`'s region of the game, laid out for the current client size.

    Drag to move, drag the bottom-right corner to resize (keeps the zoom), right-click
    to remove; each calls back on release. Locked, it lets clicks through.
    Whether it shows combines five flags: hidden (its eye), wanted (the visibility
    rule), highlighted (card hovered), editing (region dialog open) and adjusting
    (opacity slider dragged, so it shows its real opacity).
    """

    # Set from the current layout (see _select_layout), in screen pixels.
    rect: Rect  # the area shown, in client coordinates
    x: int  # the image's top-left corner on screen
    y: int
    w: int  # the image's size: the region's times the zoom
    h: int
    _guessed: bool  # the layout is a guess for a new client size, not saved yet

    def __init__(
        self,
        root: tk.Misc,
        game_hwnd: Hwnd,
        saved: SavedRegion,
        client: Rect,
        look: MirrorLook,
        on_remove: Callable[[MirrorWindow], None],
        on_changed: Callable[[MirrorWindow], None],
    ) -> None:
        self._root = root
        self.name = saved.name
        self.opacity = clamp_opacity(saved.opacity)
        self.zoom = clamp_zoom(saved.zoom)
        self.color = saved.color
        self.id = saved.id or new_id()
        self.timer = saved.timer
        # time.monotonic() of the last start, None before the first
        self._timer_start: float | None = None
        self._timer_done = False
        # Seconds counted when it paused at a logout, None unless paused (see timers.py).
        self._timer_paused: float | None = None
        self._badge: TimerBadge | None = None  # while the timer is on
        self.hidden = saved.hidden
        self.locked = False
        self._layouts = dict(saved.layouts)
        self._client = client
        self._look = look
        self._select_layout()

        self._wanted = False
        self._highlighted = False
        self._editing = False
        self._adjusting = False
        self._alpha = 0.0
        self._mapped = True
        self._tween: Tween | None = None
        self._destroyed = False
        self._rounded: bool | None = None  # corner rounding last applied to both windows

        # With rounded corners the frame is a window of its own, right behind
        # the image window (see _layout). Created first, so it starts below it.
        self._frame_win = tk.Toplevel(root)
        keep_open(self._frame_win)
        self._frame_win.overrideredirect(True)
        self._frame_win.attributes("-alpha", 0.0)
        self._frame_win.attributes("-topmost", True)
        self._frame_hwnd = win32.toplevel_hwnd(self._frame_win)
        win32.set_alpha(self._frame_hwnd, 0.0)
        win32.set_click_through(self._frame_hwnd, True)  # it is only a few pixels wide
        # Shaped by a window region (see _layout), never by Windows' rounding and its shadow.
        dwm.set_rounded_corners(self._frame_hwnd, False)
        # The frame window's shape last applied: set_ring_shape's arguments after the HWND.
        self._ring: tuple[int, int, int, tuple[int, int, int, int, int] | None] | None = None
        self._frame_win.withdraw()
        self._frame_shown = False

        self.win = tk.Toplevel(root)
        keep_open(self.win)
        self.win.overrideredirect(True)
        # Invisible from the first frame; win32.set_alpha takes over once the HWND exists.
        self.win.attributes("-alpha", 0.0)
        self.win.attributes("-topmost", True)
        self.win.geometry(f"{self.w}x{self.h}+{self.x}+{self.y}")
        self.hwnd = win32.toplevel_hwnd(self.win)

        try:
            self._thumb: Thumbnail | None = Thumbnail(self.hwnd, game_hwnd)
        except OSError:
            self.win.destroy()
            raise
        try:
            self._layout()
        except OSError:
            self.destroy()
            raise
        # Starts invisible; the App's visibility poll decides when to fade it in.
        self._hide_now()
        self.set_locked(saved.locked)
        self._sync_badge()

        self._grab_dx = self._grab_dy = 0
        self._dragged = False
        self._resizing = False
        self._on_changed = on_changed
        # <Enter> too: the pointer may land on the corner and rest there with no <Motion>.
        for sequence in ("<Enter>", "<Motion>"):
            self.win.bind(sequence, self._hover)
        self.win.bind("<Button-1>", self._grab)
        self.win.bind("<B1-Motion>", self._drag)
        self.win.bind("<ButtonRelease-1>", self._drop)
        self._on_remove = on_remove
        self.win.bind("<Button-3>", self._context_menu)

    def _context_menu(self, e: tk.Event[tk.Misc]) -> None:
        # Built on each right-click, so it follows the current language.
        menu = tk.Menu(self.win, tearoff=0)
        menu.add_command(label=tr("Remove"), command=lambda: self._on_remove(self))
        menu.tk_popup(e.x_root, e.y_root)

    # ---- inputs -------------------------------------------------------------
    def set_visible(self, wanted: bool) -> None:
        if wanted != self._wanted:
            self._wanted = wanted
            self._update()

    def set_highlighted(self, highlighted: bool) -> None:
        if highlighted != self._highlighted:
            self._highlighted = highlighted
            self._emphasis_changed()

    def set_editing(self, editing: bool) -> None:
        if editing != self._editing:
            self._editing = editing
            self._emphasis_changed()

    def _emphasized(self) -> bool:
        return self._highlighted or self._editing

    def _emphasis_changed(self) -> None:
        self._layout()
        if self._emphasized():
            self._raise()
        self._update()

    def _raise(self) -> None:
        """To the top of the always-on-top windows, the frame window just below the image."""
        # Tk drops a window's pending move when it is raised first (a hover's thicker
        # frame would grow the mirror down-right only), so moves are applied before.
        self.win.update_idletasks()
        if self._frame_shown:
            self._frame_win.lift()
        self.win.lift()
        if self._badge is not None:
            self._badge.lift()

    def set_adjusting(self, adjusting: bool) -> None:
        if adjusting != self._adjusting:
            self._adjusting = adjusting
            self._update()

    def set_opacity(self, opacity: float) -> None:
        self.opacity = clamp_opacity(opacity)
        self._update()

    def set_hidden(self, hidden: bool) -> None:
        if hidden != self.hidden:
            self.hidden = hidden
            self._update()

    def set_look(self, look: MirrorLook) -> None:
        self._look = look
        self._layout()

    def set_color(self, color: str) -> None:
        """Frame colour by name (config.FRAME_COLORS)."""
        self.color = color
        self._layout()

    def set_zoom(self, zoom: float) -> None:
        """Show the region at `zoom` times its size; the top-left corner stays put."""
        self.zoom = clamp_zoom(zoom)
        self._fit_window()
        self._layout()

    def preview(self, rect: Rect, zoom: float) -> None:
        """Show `rect` at `zoom` without keeping it as this size's layout (live preview)."""
        self.rect = rect
        self.set_zoom(zoom)

    def set_client(self, client: Rect) -> None:
        """Follow the game's client area: a new size switches layout, a move just follows."""
        if client == self._client:
            return
        old, self._client = self._client, client
        if (client.w, client.h) != (old.w, old.h):
            self._select_layout()
        else:
            self.x += client.x - old.x
            self.y += client.y - old.y
        self._layout()

    def set_region(self, rect: Rect) -> None:
        """Show `rect` (client coordinates) from now on, at this client size."""
        self.rect = rect
        self._fit_window()
        self._commit()
        self._layout()

    def resize_region(self, w: int, h: int) -> None:
        """Make the area shown w x h around its centre, inside the client area."""
        self.set_region(resize_around_center(self.rect, w, h, self._client.w, self._client.h))

    def detach(self) -> None:
        """The game window is gone: drop the thumbnail and hide until attach()."""
        self._cancel_tween()
        if self._thumb is not None:
            self._thumb.close()
            self._thumb = None
        self._wanted = False
        self._hide_now()

    def attach(self, game_hwnd: Hwnd, client: Rect) -> None:
        """Mirror a (new) game window; raises OSError if DWM refuses it."""
        self._thumb = Thumbnail(self.hwnd, game_hwnd)
        self.set_client(client)
        self._layout()

    def set_locked(self, locked: bool) -> None:
        self.locked = locked
        win32.set_click_through(self.hwnd, locked)

    def to_saved(self) -> SavedRegion:
        return SavedRegion(
            self.name,
            dict(self._layouts),
            self.opacity,
            self.hidden,
            self.locked,
            self.zoom,
            self.color,
            self.timer,
            self.id,
        )

    # ---- timer --------------------------------------------------------------
    def set_timer(self, settings: TimerSettings) -> None:
        """New timer settings; a running count stops, and starts again on the next trigger."""
        self.timer = settings
        self._timer_start, self._timer_done, self._timer_paused = None, False, None
        self._sync_badge()

    def start_timer(self, now: float) -> None:
        """A click on the region or the timer's key: count from zero again."""
        if self.timer.enabled:
            self._timer_start, self._timer_done, self._timer_paused = now, False, None
            self._refresh_badge(now)

    def restore_timer(
        self, now: float, started: float | None = None, paused: float | None = None
    ) -> None:
        """Set a pausing timer's state: running since `started`, paused at `paused`
        seconds, or not started. Past its alert time it shows as done, silently.
        """
        self._timer_start = started
        self._timer_paused = None if started is not None else paused
        elapsed = now - started if started is not None else paused
        self._timer_done = is_done(self.timer, elapsed)
        self._refresh_badge(now)

    def timer_elapsed(self, now: float) -> float | None:
        """Seconds counted since the last start, None if it never started."""
        if self._timer_paused is not None:
            return self._timer_paused
        return None if self._timer_start is None else now - self._timer_start

    def tick_timer(self, now: float) -> bool:
        """Advance the badge; True exactly once, when the alert time is reached."""
        if self._timer_start is None or self._timer_done or self._timer_paused is not None:
            return False
        if is_done(self.timer, now - self._timer_start):
            self._timer_done = True
            self._refresh_badge(now)
            return True
        self._refresh_badge(now)
        return False

    def _sync_badge(self) -> None:
        """Create the badge when the timer is on, remove it when it is off."""
        if self.timer.enabled and self._badge is None:
            self._badge = TimerBadge(self._root)
            self._place_badge()
            self._badge.set_alpha(self._badge_alpha())
            self._badge.show(self._mapped)
        elif not self.timer.enabled and self._badge is not None:
            self._badge.destroy()
            self._badge = None
        # A timer that was just set up has not started, so the time only matters later.
        self._refresh_badge(time.monotonic())

    def _refresh_badge(self, now: float) -> None:
        if self._badge is None:
            return
        if self._timer_done:
            self._badge.set_text(badge_text(self.timer, self.timer.alert), "done")
            return
        if self._timer_paused is not None:
            # Dimmed like a timer not started yet: it waits for the character's login.
            self._badge.set_text(badge_text(self.timer, self._timer_paused), "idle")
            return
        if self._timer_start is None:
            self._badge.set_text(badge_text(self.timer, None), "idle")
            return
        elapsed = now - self._timer_start
        state = "running"
        self._badge.set_text(badge_text(self.timer, elapsed), state)

    def _place_badge(self) -> None:
        if self._badge is not None:
            self._badge.place(self.x, self.y, self.w, self.h, self._border())

    def _badge_alpha(self) -> float:
        """Fades in and out with the mirror, but stays readable on a see-through one."""
        return min(1.0, self._alpha / max(self.opacity, 0.01))

    # ---- layouts ------------------------------------------------------------
    def _select_layout(self) -> None:
        """Take this client size's layout, or a guess (kept on screen) if there is none."""
        client = self._client
        key = size_key(client.w, client.h)
        self._guessed = key not in self._layouts
        layout = (
            guess_layout(self._layouts, client.w, client.h) if self._guessed else self._layouts[key]
        )
        self.rect = layout.region
        self._fit_window()
        self.x, self.y = client.x + layout.offset[0], client.y + layout.offset[1]
        if self._guessed:
            center = (client.x + client.w // 2, client.y + client.h // 2)
            bounds = win32.work_area_at(center)
            self.x, self.y = clamp_box(self.x, self.y, self.w, self.h, bounds)

    def _fit_window(self) -> None:
        self.w, self.h = scaled_size(self.rect.w, self.rect.h, self.zoom)

    def _commit(self) -> None:
        """Keep the current region and position as this client size's layout."""
        client = self._client
        self._layouts[size_key(client.w, client.h)] = Layout(
            self.rect, (self.x - client.x, self.y - client.y)
        )
        self._guessed = False

    def fade_out_and_destroy(self) -> None:
        self._wanted = self._highlighted = self._editing = False
        if not self._mapped:
            self.destroy()
            return
        self._animate_to(0.0, on_done=self.destroy)

    def destroy(self) -> None:
        if self._destroyed:
            return
        self._destroyed = True
        self._cancel_tween()
        try:
            if self._thumb is not None:
                self._thumb.close()
        finally:
            self.win.destroy()
            self._frame_win.destroy()
            if self._badge is not None:
                self._badge.destroy()

    # ---- rendering ----------------------------------------------------------
    def _target_alpha(self) -> float:
        if self.hidden or not (self._wanted or self._emphasized()):
            return 0.0
        if self._emphasized() and not self._adjusting:
            return 1.0
        return self.opacity

    def _update(self) -> None:
        target = self._target_alpha()
        if target > 0 and not self._mapped:
            self._mapped = True
            if self._frame_shown:
                self._frame_win.deiconify()
                self._frame_win.attributes("-topmost", True)
            self.win.deiconify()
            self.win.attributes("-topmost", True)
            if self._badge is not None:
                self._badge.show(True)
        self._animate_to(target)

    def _animate_to(self, target: float, on_done: Callable[[], None] | None = None) -> None:
        self._cancel_tween()

        def finished() -> None:
            self._tween = None
            if target == 0:
                self._hide_now()
            if on_done:
                on_done()

        self._tween = Tween(
            self.win, self._alpha, target, self._look.fade_ms, self._set_alpha, finished
        )

    def _cancel_tween(self) -> None:
        if self._tween is not None:
            self._tween.cancel()
            self._tween = None

    def _set_alpha(self, alpha: float) -> None:
        self._alpha = alpha
        win32.set_alpha(self.hwnd, alpha)
        win32.set_alpha(self._frame_hwnd, alpha)
        if self._badge is not None:
            self._badge.set_alpha(self._badge_alpha())

    def _hide_now(self) -> None:
        self._set_alpha(0.0)
        if self._mapped:
            self.win.withdraw()
            self._frame_win.withdraw()
            if self._badge is not None:
                self._badge.show(False)
            self._mapped = False

    def _border(self) -> int:
        """Frame width: accent when emphasized, a chosen colour always, else grey if on."""
        if self._emphasized():
            return px(HIGHLIGHT_BORDER)
        if self.color != FRAME_COLORS[0]:
            return px(COLOR_BORDER)
        return px(MIRROR_BORDER) if self._look.frame else 0

    def _layout(self) -> None:
        """Size and place the image at (x, y) with a `border`-wide frame around it.

        Square and untinted: one window, whose background shows as the frame. Rounded
        or tinted: the frame is a second window behind, shaped as a ring (see
        docs/architecture.md, "Mirrors: DWM thumbnails").
        """
        border = self._border()
        color = theme.frame_color(self.color)
        rounded = self._look.rounded
        tinted = self._look.tint and self.color != FRAME_COLORS[0]
        if rounded != self._rounded:
            self._rounded = rounded
            dwm.set_rounded_corners(self.hwnd, rounded)
        self.win.configure(bg=color)
        if self._split():
            self._place(self.win, self._image_box(0))
            if border:
                self._frame_win.configure(bg=color)
                self._place(self._frame_win, self._image_box(border))
                self._shape_frame(border, rounded, tinted)
            self._show_frame_window(border > 0)
            image = Rect(0, 0, self.w, self.h)
        else:
            self._show_frame_window(False)
            self._place(self.win, self._image_box(border))
            image = Rect(border, border, self.w, self.h)
        if self._thumb is not None:  # None while the game window is gone
            self._thumb.show(self.rect, image)
        self._place_badge()

    def _split(self) -> bool:
        """Whether the frame is a window of its own (see _layout)."""
        tinted = self._look.tint and self.color != FRAME_COLORS[0]
        return self._look.rounded or tinted

    def _shape_frame(self, border: int, rounded: bool, tinted: bool) -> None:
        """The frame window as a ring around the image, or solid when tinted."""
        radius = round(ROUND_SMALL_RADIUS * win32.dpi_scale(self.hwnd)) if rounded else 0
        hole = None if tinted else (border, border, self.w, self.h, radius)
        ring = (self.w + 2 * border, self.h + 2 * border, radius + border if radius else 0, hole)
        if ring != self._ring:
            self._ring = ring
            # Reshaping makes Tk re-read the window's place, dropping a move it hasn't
            # applied yet (a frame that changes size would stay behind), so apply it first.
            self._frame_win.update_idletasks()
            win32.set_ring_shape(self._frame_hwnd, *ring)

    def _image_box(self, margin: int) -> tuple[int, int, int, int]:
        """(x, y, w, h) of the image grown by `margin` on every side, in screen coordinates."""
        return self.x - margin, self.y - margin, self.w + 2 * margin, self.h + 2 * margin

    @staticmethod
    def _place(win: tk.Toplevel, box: tuple[int, int, int, int]) -> None:
        x, y, w, h = box
        win.geometry(f"{w}x{h}+{x}+{y}")

    def _show_frame_window(self, shown: bool) -> None:
        if shown == self._frame_shown:
            return
        self._frame_shown = shown
        if not self._mapped:
            return  # _update maps it along with the image window
        if shown:
            self._frame_win.deiconify()
            self._frame_win.attributes("-topmost", True)
            self._raise()  # keep the image on top of its frame
        else:
            self._frame_win.withdraw()

    # ---- dragging -----------------------------------------------------------
    # Locked mirrors are click-through, so these only guard against stray events.
    def _in_grip(self, e: tk.Event[tk.Misc]) -> bool:
        grip = px(RESIZE_GRIP)
        return e.x >= self.win.winfo_width() - grip and e.y >= self.win.winfo_height() - grip

    def _hover(self, e: tk.Event[tk.Misc]) -> None:
        if not (self._dragged or self._resizing):
            self.win.configure(cursor="size_nw_se" if self._in_grip(e) else "")

    def _grab(self, e: tk.Event[tk.Misc]) -> None:
        if self.locked:
            return
        self._dragged = False
        self._resizing = self._in_grip(e)
        self._grab_dx, self._grab_dy = e.x_root - self.x, e.y_root - self.y

    def _drag(self, e: tk.Event[tk.Misc]) -> None:
        if self.locked:
            return
        self._dragged = True
        if self._resizing:
            zoom = zoom_for_width(e.x_root - self.x, self.rect.w, ZOOM_RANGE)
            if zoom != self.zoom:
                self.set_zoom(zoom)
            return
        self.x, self.y = e.x_root - self._grab_dx, e.y_root - self._grab_dy
        border = self._border()
        if self._split():
            self.win.geometry(f"+{self.x}+{self.y}")
            self._frame_win.geometry(f"+{self.x - border}+{self.y - border}")
        else:
            self.win.geometry(f"+{self.x - border}+{self.y - border}")
        self._place_badge()

    def _drop(self, _e: tk.Event[tk.Misc]) -> None:
        # A click without a drag must not turn a guessed layout into a saved one.
        if not self._dragged:
            self._resizing = False
            return
        if not self._resizing:
            self._commit()  # a move; the zoom is not part of the layout
        self._dragged = self._resizing = False
        self._on_changed(self)
