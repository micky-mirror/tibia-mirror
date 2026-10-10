"""A paragraph of text where each part can have its own colour."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Sequence

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import LABEL_INSET


class RichParagraph(tk.Frame):
    """A paragraph where each part has its own colour. It lines up with a tk.Label.

    `text_parts` is a list of (text, colour). Long lines break at `width` pixels.
    """

    def __init__(self, parent: tk.Misc, text_parts: Sequence[tuple[str, str]], width: int) -> None:
        # A text box takes its size in letters, not in pixels. So it fills this frame,
        # and the frame has the size in pixels. The real height is set in _on_resize.
        super().__init__(parent, bg=theme.BG, width=width + 2 * LABEL_INSET, height=1)
        # Keep the size given above; without this the frame takes the size of the text box.
        self.pack_propagate(False)
        self._add_text_box()
        self._add_text_parts(text_parts)
        self._remove_text_box_actions()
        self._text.bind("<Configure>", self._on_resize)

    def _add_text_box(self) -> None:
        self._text = tk.Text(
            self,
            font=theme.FONT,
            bg=theme.BG,
            bd=0,
            highlightthickness=0,
            padx=LABEL_INSET,
            pady=LABEL_INSET,
            wrap="word",
            cursor="",
        )
        self._text.pack(fill="both", expand=True)

    def _add_text_parts(self, text_parts: Sequence[tuple[str, str]]) -> None:
        """Put each part into the text box in its colour, then make the box read-only."""
        for number, (text, colour) in enumerate(text_parts):
            tag = f"part{number}"
            self._text.tag_configure(tag, foreground=colour)
            self._text.insert("end", text, tag)
        self._text.configure(state="disabled")

    def _remove_text_box_actions(self) -> None:
        """Drop what a text box does on its own: selecting with the mouse, keys, its own scrolling.

        The text then acts like a label, and the mouse wheel reaches the page under it.
        """
        # Tk looks for the action of an event in these groups, in this order.
        # The normal list also has "Text", the group with the actions of every text box.
        window = self._text.winfo_toplevel()
        self._text.bindtags((str(self._text), str(window), "all"))

    def _on_resize(self, event: tk.Event[tk.Text]) -> None:
        """Make the frame as high as its lines of text.

        Tk calls this when the text box has a size.
        """
        line_height = tkfont.Font(font=theme.FONT).metrics("linespace")
        self.configure(height=self._line_count() * line_height + 2 * LABEL_INSET)

    def _line_count(self) -> int:
        """How many lines the text takes on screen, after long lines are broken."""
        counted = self._text.count("1.0", "end", "displaylines")
        return counted[0] if isinstance(counted, tuple) else (counted or 1)
