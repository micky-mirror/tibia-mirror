"""A segmented control: a few options side by side, the chosen one on an accent pill."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 28  # of the track
INSET = 2  # between the track and the pills inside it
TEXT_PAD = 14  # left and right of each text, inside its pill
TRACK_RADIUS = 8
PILL_RADIUS = 6


class SegmentedControl:
    """A few options side by side in a rounded track, drawn on a canvas. One of them is chosen."""

    def __init__(
        self,
        canvas: tk.Canvas,
        right: int,
        middle_y: int,
        options: Sequence[tuple[str, str]],
        selected: str,
        on_change: Callable[[str], None],
    ) -> None:
        self._canvas = canvas
        self._right = right  # where the track ends on the canvas
        self._middle_y = middle_y  # the middle line of the track
        self._options = options  # (key, text) of each option, from left to right
        self._selected = selected  # the key of the chosen option
        self._on_change = on_change  # called with the key of the option the user chooses
        self._font = tkfont.Font(font=theme.FONT)  # measures the texts
        self._boxes = self._get_boxes()  # the place of the pill of each option, by key
        # draw control parts
        self._draw_track()
        self._add_pill()
        self._add_texts()
        self._update_pill()
        self._update_texts()

    def _draw_track(self) -> None:
        """The rounded shape all options sit in."""
        width = self._get_width()
        self._track_image = rounded_image(
            self._canvas,
            width=width,
            height=px(HEIGHT),
            radius=px(TRACK_RADIUS),
            colour=theme.SURFACE_HI,
            background=theme.SURFACE,
        )

        self._canvas.create_image(
            self._right - width, self._get_top_y(), anchor="nw", image=self._track_image
        )

    def _add_pill(self) -> None:
        """The accent shape behind the chosen option."""
        self._pill_image: tk.PhotoImage | None = None  # drawn again for each chosen option
        self._pill = self._canvas.create_image(0, 0, anchor="nw")

    def _add_texts(self) -> None:
        """The text of each option, in the middle of its pill."""
        self._text_items: dict[str, int] = {}  # the canvas item of each text, by key

        for key, text in self._options:
            left, _top, right, _bottom = self._boxes[key]
            middle_x = (left + right) / 2

            self._text_items[key] = self._canvas.create_text(
                middle_x, self._middle_y, text=text, font=theme.FONT
            )

    def _update_pill(self) -> None:
        """Put the pill behind the chosen option, as wide as that option."""
        left, top, right, bottom = self._boxes[self._selected]

        self._pill_image = rounded_image(
            self._canvas,
            width=right - left,
            height=bottom - top,
            radius=px(PILL_RADIUS),
            colour=theme.ACCENT,
            background=theme.SURFACE_HI,
        )
        self._canvas.itemconfigure(self._pill, image=self._pill_image)
        self._canvas.coords(self._pill, left, top)

    def _update_texts(self) -> None:
        """Each text in the colour of its option's state."""
        for key, item in self._text_items.items():
            self._canvas.itemconfigure(item, fill=self._get_text_colour(key))

    def _get_text_colour(self, key: str) -> str:
        """On the accent for the chosen option, grey for the others."""
        if key == self._selected:
            return theme.ON_ACCENT

        return theme.SUBTEXT

    def _get_boxes(self) -> dict[str, Box]:
        """The place of the pill of each option: side by side, each as wide as its text."""
        inset = px(INSET)
        top = self._get_top_y() + inset
        bottom = top + px(HEIGHT) - 2 * inset
        left = self._right - self._get_width() + inset
        boxes: dict[str, Box] = {}

        for key, text in self._options:
            right = left + self._get_pill_width(text)
            boxes[key] = (left, top, right, bottom)
            left = right

        return boxes

    def _get_width(self) -> int:
        """Room for every pill, with the inset at both ends."""
        pills_width = sum(self._get_pill_width(text) for _key, text in self._options)

        return pills_width + 2 * px(INSET)

    def _get_pill_width(self, text: str) -> int:
        return self._font.measure(text) + 2 * px(TEXT_PAD)

    def _get_top_y(self) -> int:
        """The top of the track."""
        return self._middle_y - px(HEIGHT) // 2
