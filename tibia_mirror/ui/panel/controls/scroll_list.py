"""A scroll list: a column that scrolls, with a thin bar that shows only when needed."""

from __future__ import annotations

import tkinter as tk

from tibia_mirror.core.geometry import scroll_thumb
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
BAR_WIDTH = 6
BAR_GAP = 7  # between the column and the bar
MIN_THUMB_HEIGHT = 24


class ScrollList(tk.Frame):
    """A column that scrolls when its content does not fit. The content goes in `inner`."""

    def __init__(self, parent: tk.Misc, *, width: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width  # the width of the column, in pixels
        self._offset = 0  # how far the content is scrolled up, in pixels
        self._thumb_images: dict[str, tk.PhotoImage] = {}  # for the current thumb height
        self._is_hovered = False  # True while the pointer is over the bar
        self._is_dragging = False  # True from a press on the thumb until the button goes up
        # draw scroll list parts
        self._add_view()
        self._add_inner()
        self._add_bar()
        self._bind_events()

    def _add_view(self) -> None:
        """The frame that shows the visible part of the column and cuts off the rest."""
        self._view = tk.Frame(self, width=self._width, bg=theme.BG)
        self._view.pack(side="left", fill="y")

    def _add_inner(self) -> None:
        self.inner = tk.Frame(self._view, bg=theme.BG)
        self.inner.place(x=0, y=0, width=self._width)

    def _add_bar(self) -> None:
        """The thin bar beside the column, with the thumb that shows where the view is."""
        self._bar = tk.Canvas(self, width=px(BAR_WIDTH), bg=theme.BG, highlightthickness=0, bd=0)
        self._bar.pack(side="left", fill="y", padx=(px(BAR_GAP), 0))
        self._thumb = self._bar.create_image(0, 0, anchor="nw", state="hidden")

    def _bind_events(self) -> None:
        self.inner.bind("<Configure>", self._on_resize)
        self._view.bind("<Configure>", self._on_resize)
        self._bar.bind("<Configure>", self._on_resize)

    def _on_resize(self, _event: tk.Event[tk.Misc]) -> None:
        self._scroll_to(self._offset)

    def _scroll_to(self, offset: int) -> None:
        """Scroll the content up by `offset` pixels, kept between the top and the bottom."""
        lowest_offset = self.inner.winfo_reqheight() - self._view.winfo_height()
        self._offset = max(0, min(offset, lowest_offset))
        self.inner.place_configure(y=-self._offset)
        self._update_thumb()

    def _update_thumb(self) -> None:
        """Place the thumb where the view is, or hide it when the whole column fits."""
        content_height = self.inner.winfo_reqheight()
        first = self._offset / content_height
        last = (self._offset + self._view.winfo_height()) / content_height
        track_height = self._bar.winfo_height()
        thumb_box = scroll_thumb(first, last, track_height, px(MIN_THUMB_HEIGHT))
        if thumb_box is None:
            self._bar.itemconfigure(self._thumb, state="hidden")
            return

        top, height = thumb_box
        self._update_thumb_images(height)
        image = self._thumb_images[self._get_look()]

        self._bar.itemconfigure(self._thumb, image=image, state="normal")
        self._bar.coords(self._thumb, 0, top)

    def _update_thumb_images(self, height: int) -> None:
        """Draw the thumb in each of its looks again when its height changed."""
        if self._thumb_images and self._thumb_images["normal"].height() == height:
            return

        self._thumb_images = {
            "normal": self._get_thumb_image(height, theme.SURFACE_HI),
            "active": self._get_thumb_image(height, theme.SUBTEXT),
        }

    def _get_thumb_image(self, height: int, colour: str) -> tk.PhotoImage:
        width = px(BAR_WIDTH)
        return rounded_image(
            self._bar,
            width=width,
            height=height,
            radius=width // 2,
            colour=colour,
            background=theme.BG,
        )

    def _get_look(self) -> str:
        if self._is_hovered or self._is_dragging:
            return "active"
        return "normal"
