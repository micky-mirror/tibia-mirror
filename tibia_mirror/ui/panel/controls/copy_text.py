"""A copy text: a text with a copy icon after it. A click puts the text on the clipboard."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.core.geometry import Box
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import icons, theme
from tibia_mirror.ui.base.scale import LABEL_INSET, px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.panel.controls.tooltip import Tip, Tooltip

# Sizes at 100% display scaling; px() scales them where they are used.
ICON_GAP = 6  # between the text and the icon
SLACK = 2  # room above, below and after the text and the icon, so their edges are easy to hit


class CopyText(tk.Canvas):
    """A text with a copy icon after it. A click copies the whole text, even when cut short."""

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        *,
        text_colour: str,
        background: str,
        is_small: bool = False,
        inset: int = LABEL_INSET,
        max_width: int | None = None,
    ) -> None:
        super().__init__(parent, bg=background, highlightthickness=0, bd=0, cursor="hand2")
        self._text = text  # copied in full, even when it is shown cut short
        self._text_colour = text_colour
        self._inset = inset  # from the left side to the text, to line up with the labels around it
        self._max_width = max_width  # a longer text is cut short with "…"; None for no limit
        self._text_font, self._icon_font = self._get_fonts(is_small)
        self._shown_text = self._get_shown_text()  # the text as it is shown, cut short if too long
        self._tooltip = Tooltip(self.winfo_toplevel())
        self._is_hovered = False
        self._is_pressed = False  # True from a press on the copy text until the button goes up
        self._is_copied = False  # True after a click, until the pointer leaves
        # draw copy text parts
        self._add_text()
        self._add_icon()
        self._fit_size()
        self._update_look()
        self._bind_events()

    def _add_text(self) -> None:
        self._text_item = self.create_text(
            self._inset,
            self._get_middle_y(),
            text=self._shown_text,
            anchor="w",
            font=self._text_font,
        )

    def _add_icon(self) -> None:
        """The copy icon, a small gap after the text."""
        self._icon_item = self.create_text(
            self._get_icon_x(),
            self._get_middle_y(),
            text=icons.COPY,
            anchor="w",
            font=self._icon_font,
        )

    def _fit_size(self) -> None:
        """Make the canvas as big as the text and the icon, with the slack around them."""
        width = self._get_icon_x() + self._icon_font.measure(icons.COPY) + px(SLACK)

        self.configure(width=width, height=self._get_height())

    def _bind_events(self) -> None:
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.bind("<Destroy>", self._on_destroy)

    def _on_mouse_enter(self, event: tk.Event[tk.Canvas]) -> None:
        self._is_hovered = True
        self._update_look()
        self._tooltip.show(Tip(tr("Copy")), self._get_screen_box())

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        self._is_hovered = False
        self._is_copied = False  # the next visit offers to copy again
        self._update_look()
        self._tooltip.hide()

    def _on_mouse_down(self, event: tk.Event[tk.Canvas]) -> None:
        self._is_pressed = True

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        # a click only when the mouse button went down and up on the copy text
        is_click = self._is_pressed and self._is_hovered
        self._is_pressed = False

        if is_click:
            self._copy()

    def _on_destroy(self, event: tk.Event[tk.Canvas]) -> None:
        # the hint is a window of its own, so it must close with the copy text
        self._tooltip.hide()

    def _copy(self) -> None:
        """Put the whole text on the clipboard, and say so with a check mark and the hint."""
        self.clipboard_clear()
        self.clipboard_append(self._text)
        self._is_copied = True
        self._update_look()
        self._tooltip.show(Tip(tr("Copied")), self._get_screen_box())

    def _update_look(self) -> None:
        """The text and the icon in the colours of the current state."""
        text_colour = theme.ACCENT if self._is_hovered else self._text_colour
        icon, icon_colour = self._get_icon_look()

        self.itemconfigure(self._text_item, fill=text_colour)
        self.itemconfigure(self._icon_item, text=icon, fill=icon_colour)

    def _get_icon_look(self) -> tuple[str, str]:
        """A green check mark after a copy, else the copy icon: blue while hovered, grey if not."""
        if self._is_copied:
            return icons.CHECK, theme.GREEN

        if self._is_hovered:
            return icons.COPY, theme.ACCENT

        return icons.COPY, theme.SUBTEXT

    def _get_screen_box(self) -> Box:
        """The place of the copy text on the screen. The hint opens under it."""
        left = self.winfo_rootx()
        top = self.winfo_rooty()

        return left, top, left + self.winfo_width(), top + self.winfo_height()

    def _get_fonts(self, is_small: bool) -> tuple[tkfont.Font, tkfont.Font]:
        """The font of the text and the font of the icon. A small copy text has smaller ones."""
        if is_small:
            return tkfont.Font(font=theme.FONT_SMALL), tkfont.Font(font=theme.FONT_ICON_SMALL)

        return tkfont.Font(font=theme.FONT), tkfont.Font(font=theme.FONT_ICON)

    def _get_shown_text(self) -> str:
        """The text, cut short with "…" when the text and the icon would pass `max_width`."""
        if self._max_width is None:
            return self._text

        icon_room = px(ICON_GAP) + self._icon_font.measure(icons.COPY) + px(SLACK)
        text_room = self._max_width - self._inset - icon_room

        return elide(self._text, self._text_font, text_room)

    def _get_icon_x(self) -> int:
        """Where the icon starts: after the shown text and the gap."""
        text_width: int = self._text_font.measure(self._shown_text)

        return self._inset + text_width + px(ICON_GAP)

    def _get_height(self) -> int:
        """As high as the taller of the two fonts, with the slack above and below."""
        text_height: int = self._text_font.metrics("linespace")
        icon_height: int = self._icon_font.metrics("linespace")

        return max(text_height, icon_height) + 2 * px(SLACK)

    def _get_middle_y(self) -> float:
        return self._get_height() / 2
