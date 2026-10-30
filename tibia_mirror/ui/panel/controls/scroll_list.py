"""A scroll list: a column that scrolls, with a thin bar that shows only when needed."""

from __future__ import annotations

import tkinter as tk

from tibia_mirror.core.geometry import scroll_fraction, scroll_thumb
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
BAR_WIDTH = 6
BAR_GAP = 7  # between the column and the bar
MIN_THUMB_HEIGHT = 24
WHEEL_STEP = 24  # how far one notch of the mouse wheel scrolls

NOTCH_DELTA = 120  # the delta Windows gives for one notch of the mouse wheel
PAGE_PART = 0.9  # a click beside the thumb scrolls this part of the view, like Tk does


class ScrollList(tk.Frame):
    """A column that scrolls when its content does not fit. The content goes in `inner`."""

    def __init__(self, parent: tk.Misc, *, width: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width  # the width of the column, in pixels
        self._offset = 0  # how far the content is scrolled up, in pixels
        self._thumb_box: tuple[int, int] | None = None  # (top, height) while the thumb shows
        self._thumb_images: dict[str, tk.PhotoImage] = {}  # for the current thumb height
        self._is_hovered = False  # True while the pointer is over the bar
        self._is_dragging = False  # True from a press on the thumb until the button goes up
        self._drag_offset = 0  # from the top of the thumb to the pointer, while dragging
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
        self._bar.bind("<Enter>", self._on_mouse_enter)
        self._bar.bind("<Leave>", self._on_mouse_leave)
        self._bar.bind("<ButtonPress-1>", self._on_mouse_down)
        self._bar.bind("<B1-Motion>", self._on_mouse_drag)
        self._bar.bind("<ButtonRelease-1>", self._on_mouse_up)
        # every widget has its window in its bindtags, so this hears the wheel over the content
        self.winfo_toplevel().bind("<MouseWheel>", self._on_mouse_wheel, add="+")

    def _on_resize(self, _event: tk.Event[tk.Misc]) -> None:
        self._scroll_to(self._offset)

    def _on_mouse_enter(self, _event: tk.Event[tk.Misc]) -> None:
        self._is_hovered = True
        self._update_thumb()

    def _on_mouse_leave(self, _event: tk.Event[tk.Misc]) -> None:
        self._is_hovered = False
        self._update_thumb()

    def _on_mouse_down(self, event: tk.Event[tk.Misc]) -> None:
        if self._thumb_box is None:
            return

        top, height = self._thumb_box
        if top <= event.y < top + height:
            self._is_dragging = True
            self._drag_offset = event.y - top
            self._update_thumb()
            return

        page = int(self._view.winfo_height() * PAGE_PART)
        direction = -1 if event.y < top else 1
        self._scroll_to(self._offset + direction * page)

    def _on_mouse_drag(self, event: tk.Event[tk.Misc]) -> None:
        if not self._is_dragging or self._thumb_box is None:
            return

        content_height = self.inner.winfo_reqheight()
        visible = self._view.winfo_height() / content_height
        thumb_top = event.y - self._drag_offset
        first = scroll_fraction(thumb_top, self._thumb_box[1], self._bar.winfo_height(), visible)

        self._scroll_to(round(first * content_height))

    def _on_mouse_up(self, _event: tk.Event[tk.Misc]) -> None:
        self._is_dragging = False
        self._update_thumb()

    def _on_mouse_wheel(self, event: tk.Event[tk.Misc]) -> None:
        if not self._contains_pointer(event.x_root, event.y_root):
            return

        distance = round(event.delta * px(WHEEL_STEP) / NOTCH_DELTA)
        self._scroll_to(self._offset - distance)

    def _contains_pointer(self, position_x: int, position_y: int) -> bool:
        widget = self.winfo_containing(position_x, position_y)
        while widget is not None:
            if widget is self:
                return True
            widget = widget.master
        return False

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
        self._thumb_box = scroll_thumb(first, last, track_height, px(MIN_THUMB_HEIGHT))
        if self._thumb_box is None:
            self._bar.itemconfigure(self._thumb, state="hidden")
            return

        top, height = self._thumb_box
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
