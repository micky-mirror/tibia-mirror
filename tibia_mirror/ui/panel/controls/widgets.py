"""Custom Tk widgets, mostly drawn on a canvas for rounded, anti-aliased shapes."""

from __future__ import annotations

import tkinter as tk

from tibia_mirror.core.geometry import scroll_fraction, scroll_thumb
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels
from tibia_mirror.ui.base.scale import px


class ScrollList(tk.Frame):
    """A scrollable column: put children in `self.inner`.

    The thin scrollbar shows only when needed; the wheel scrolls anywhere over it.
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    BAR_WIDTH = 6
    GUTTER = 7
    MIN_THUMB = 24
    WHEEL_STEP = 24  # pixels per wheel notch
    MAX_CACHED_THUMBS = 32

    def __init__(self, parent: tk.Misc, *, width: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width
        self.view = tk.Canvas(
            self, width=width, bg=theme.BG, highlightthickness=0, bd=0, yscrollincrement=1
        )
        self.view.pack(side="left", fill="y")
        self.bar = tk.Canvas(
            self, width=px(self.BAR_WIDTH), bg=theme.BG, highlightthickness=0, bd=0
        )
        self.bar.pack(side="left", fill="y", padx=(px(self.GUTTER), 0))
        self.inner = tk.Frame(self.view, bg=theme.BG)
        self.view.create_window(0, 0, window=self.inner, anchor="nw", width=width)

        self._thumb = self.bar.create_image(0, 0, anchor="nw", state="hidden")
        self._thumb_images: dict[tuple[int, bool], tk.PhotoImage] = {}
        self._thumb_box: tuple[int, int] | None = None  # (top, height) while visible
        self._drag_offset: int | None = None
        self._hovered = False

        self.inner.bind("<Configure>", lambda e: self._content_changed())
        self.view.bind("<Configure>", lambda e: self._content_changed())
        self.view.configure(yscrollcommand=lambda first, last: self._draw_thumb())
        self.bar.bind("<ButtonPress-1>", self._press)
        self.bar.bind("<B1-Motion>", self._drag)
        self.bar.bind("<ButtonRelease-1>", self._release)
        self.bar.bind("<Enter>", lambda e: self._set_hovered(True))
        self.bar.bind("<Leave>", lambda e: self._set_hovered(False))
        # Every widget in the window carries the toplevel in its bindtags, so
        # this sees wheel events over the cards too; _wheel filters by position.
        self.winfo_toplevel().bind("<MouseWheel>", self._wheel, add="+")

    def _content_changed(self) -> None:
        self.view.configure(scrollregion=(0, 0, self._width, self.inner.winfo_reqheight()))
        if self.inner.winfo_reqheight() <= self.view.winfo_height():
            self.view.yview_moveto(0)
        self._draw_thumb()

    def _draw_thumb(self) -> None:
        first, last = self.view.yview()
        box = scroll_thumb(first, last, self.bar.winfo_height(), px(self.MIN_THUMB))
        self._thumb_box = box
        if box is None:
            self.bar.itemconfigure(self._thumb, state="hidden")
            return
        top, height = box
        active = self._hovered or self._drag_offset is not None
        self.bar.itemconfigure(self._thumb, image=self._thumb_image(height, active), state="normal")
        self.bar.coords(self._thumb, 0, top)

    def _thumb_image(self, height: int, active: bool) -> tk.PhotoImage:
        key = (height, active)
        if key not in self._thumb_images:
            if len(self._thumb_images) >= self.MAX_CACHED_THUMBS:
                self._thumb_images.clear()
            bar_width = px(self.BAR_WIDTH)
            style = ButtonStyle(
                fill=theme.SUBTEXT if active else theme.SURFACE_HI, radius=bar_width // 2
            )
            rows = button_pixels(bar_width, height, style, theme.BG)
            self._thumb_images[key] = photo(self.bar, rows)
        return self._thumb_images[key]

    def _set_hovered(self, hovered: bool) -> None:
        self._hovered = hovered
        self._draw_thumb()

    def _press(self, e: tk.Event[tk.Canvas]) -> None:
        if self._thumb_box is None:
            return
        top, height = self._thumb_box
        if top <= e.y < top + height:
            self._drag_offset = e.y - top
            self._draw_thumb()
        else:
            self.view.yview_scroll(-1 if e.y < top else 1, "pages")

    def _drag(self, e: tk.Event[tk.Canvas]) -> None:
        if self._drag_offset is None or self._thumb_box is None:
            return
        first, last = self.view.yview()
        self.view.yview_moveto(
            scroll_fraction(
                e.y - self._drag_offset,
                self._thumb_box[1],
                self.bar.winfo_height(),
                last - first,
            )
        )

    def _release(self, _event: tk.Event[tk.Canvas]) -> None:
        self._drag_offset = None
        self._draw_thumb()

    def _wheel(self, e: tk.Event[tk.Misc]) -> None:
        if self._thumb_box is None or not self._contains_pointer(e):
            return
        self.view.yview_scroll(round(-e.delta * px(self.WHEEL_STEP) / 120), "units")

    def _contains_pointer(self, e: tk.Event[tk.Misc]) -> bool:
        w = self.winfo_containing(e.x_root, e.y_root)
        while w is not None:
            if w is self:
                return True
            w = w.master
        return False
