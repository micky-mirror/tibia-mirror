"""A step of the help on an empty Mirrors page."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Sequence
from dataclasses import dataclass

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import outlined_image, rounded_image
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
PAD = 16  # between the outline and the content
RADIUS = 8  # of the rounded corners, as on the mirror cards
CIRCLE_SIZE = 26  # of the circle with the number
TEXT_GAP = 14  # between the circle and the texts
HINT_GAP = 4  # between the title and the hint
DIVIDER_GAP = 12  # above and below the line between two parts of the hint
TITLE_RAISE = 5  # the space the font keeps above its letters


@dataclass(frozen=True)
class HintLine:
    """A part of the hint of a help step, with an optional name."""

    text: str
    name: str = ""
    name_colour: str | None = None  # a theme colour; None draws it like the text


class HelpStep(tk.Canvas):
    """A numbered step of the help, with a title and a hint."""

    def __init__(
        self,
        parent: tk.Misc,
        width: int,
        number: int,
        title: str,
        hint_lines: Sequence[HintLine],
    ) -> None:
        super().__init__(parent, width=width, bg=theme.BG, highlightthickness=0, bd=0)
        self._width = width
        self._hint_font = tkfont.Font(font=theme.FONT)
        self._text_x = px(PAD) + px(CIRCLE_SIZE) + px(TEXT_GAP)  # where the texts start
        # draw the step, then the outline as tall as it
        self._draw_number(number)
        title_end_y = self._draw_title(title)
        hint_end_y = self._draw_hint(hint_lines, title_end_y)
        self._draw_outline(hint_end_y + px(PAD))

    def _draw_number(self, number: int) -> None:
        """The number of the step."""
        size = px(CIRCLE_SIZE)
        self._circle_image = rounded_image(
            self,
            width=size,
            height=size,
            radius=size // 2,
            colour=theme.ACCENT,
            background=theme.BG,
        )
        self.create_image(px(PAD), px(PAD), image=self._circle_image, anchor="nw")
        self.create_text(
            px(PAD) + size // 2,
            px(PAD) + size // 2,
            text=str(number),
            font=theme.FONT_BOLD,
            fill=theme.ON_ACCENT,
        )

    def _draw_title(self, title: str) -> int:
        """The title of the step. Return the y where it ends."""
        title_item = self.create_text(
            self._text_x,
            px(PAD) - px(TITLE_RAISE),  # the letters start level with the circle
            text=title,
            anchor="nw",
            font=theme.FONT_HEADING,
            fill=theme.TEXT,
        )
        title_end_y: int = self.bbox(title_item)[3]
        return title_end_y

    def _draw_hint(self, hint_lines: Sequence[HintLine], title_end_y: int) -> int:
        """The hint under the title. Return the y where it ends."""
        line_start_y = title_end_y + px(HINT_GAP)

        for index, line in enumerate(hint_lines):
            # a named line after other lines starts a new part of the hint
            if line.name and index > 0:
                line_start_y = self._draw_divider(line_start_y)

            line_start_y = self._draw_hint_line(line, line_start_y)

        return line_start_y

    def _draw_divider(self, top_y: int) -> int:
        """A line between two parts of the hint. Return the y where its space ends."""
        line_y = top_y + px(DIVIDER_GAP)
        text_end_x = self._width - px(PAD)

        self.create_line(self._text_x, line_y, text_end_x, line_y, fill=theme.SURFACE_HI)
        return line_y + px(DIVIDER_GAP)

    def _draw_hint_line(self, line: HintLine, line_start_y: int) -> int:
        """One line of the hint. Return the y where it ends."""
        text_start_y = self._draw_name(line, line_start_y) if line.name else line_start_y
        text_item = self.create_text(
            self._text_x,
            text_start_y,
            text=line.text,
            anchor="nw",
            width=self._width - self._text_x - px(PAD),
            font=self._hint_font,
            fill=theme.SUBTEXT,
        )
        line_end_y: int = self.bbox(text_item)[3]
        return line_end_y

    def _draw_name(self, line: HintLine, line_start_y: int) -> int:
        """The name of a hint line. Return the y where it ends."""
        name_item = self.create_text(
            self._text_x,
            line_start_y,
            text=line.name,
            anchor="nw",
            font=self._hint_font,
            fill=line.name_colour or theme.SUBTEXT,
        )
        name_end_y: int = self.bbox(name_item)[3]
        return name_end_y

    def _draw_outline(self, height: int) -> None:
        """The outline around the step."""
        self.configure(height=height)
        self._outline_image = outlined_image(
            self,
            width=self._width,
            height=height,
            radius=px(RADIUS),
            colour=theme.BG,
            border=theme.SURFACE_HI,
            background=theme.BG,
        )
        outline = self.create_image(0, 0, image=self._outline_image, anchor="nw")
        self.tag_lower(outline)
