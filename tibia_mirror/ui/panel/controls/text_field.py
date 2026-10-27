"""A text field: a rounded box to type one line of text in."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import outlined_image
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 36
TEXT_PAD = 10  # left and right of the text, inside the box
RADIUS = 8


class TextField(tk.Canvas):
    """A rounded box with one line of text to type. Its border shows focus and errors."""

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        *,
        width: int,
        background: str,
        is_allowed: Callable[[str], bool],
        on_change: Callable[[str], None],
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=px(HEIGHT),
            bg=background,
            highlightthickness=0,
            bd=0,
            cursor="xterm",
        )
        self._width = width
        self._background = background  # the colour around the box; its round corners blend into it
        self._text = tk.StringVar(self, text)
        self._is_allowed = is_allowed  # True when the field may hold this text after a key
        self._on_change = on_change  # called with the text after each change
        self._is_focused = False
        self._is_error = False
        # draw field parts
        self._add_box()
        self._add_entry()
        self._bind_events()
        self._update_box()

    def get_text(self) -> str:
        return self._text.get()

    def set_error(self, is_error: bool) -> None:
        """Show the box with a red border, or with its normal one again."""
        self._is_error = is_error
        self._update_box()

    def select_all(self) -> None:
        """Put the keys in the field with the whole text selected, so typing replaces it."""
        self._entry.focus_set()
        self._entry.select_range(0, "end")
        self._entry.icursor("end")

    def _add_box(self) -> None:
        """The rounded box, with its border in each of its looks."""
        self._box_images = {
            "normal": self._get_box_image(theme.SURFACE_HI),
            "focused": self._get_box_image(theme.ACCENT),
            "error": self._get_box_image(theme.RED),
        }
        self._box = self.create_image(0, 0, anchor="nw")

    def _add_entry(self) -> None:
        """The Tk entry the text is typed in, inside the box with room left and right."""
        text_pad = px(TEXT_PAD)
        # Tk asks before every change. %P: the text the field would have after it.
        allowed_text = (self.register(self._is_allowed), "%P")
        self._entry = tk.Entry(
            self,
            textvariable=self._text,
            validate="key",
            validatecommand=allowed_text,
            font=theme.FONT,
            bg=theme.SURFACE,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,  # the blinking cursor
            selectbackground=theme.ACCENT,
            selectforeground=theme.ON_ACCENT,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )

        self.create_window(
            text_pad,
            px(HEIGHT) // 2,
            window=self._entry,
            anchor="w",
            width=self._width - 2 * text_pad,
        )

    def _bind_events(self) -> None:
        self._text.trace_add("write", self._on_text_changed)
        self._entry.bind("<FocusIn>", self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        # a click on the room around the text puts the keys in the entry too
        self.bind("<ButtonPress-1>", self._on_mouse_down)

    def _on_text_changed(self, *trace_details: str) -> None:
        self._on_change(self._text.get())

    def _on_focus_in(self, event: tk.Event[tk.Entry]) -> None:
        self._is_focused = True
        self._update_box()

    def _on_focus_out(self, event: tk.Event[tk.Entry]) -> None:
        self._is_focused = False
        self._update_box()

    def _on_mouse_down(self, event: tk.Event[tk.Canvas]) -> None:
        self._entry.focus_set()

    def _update_box(self) -> None:
        """Show the box with the border of its current look."""
        self.itemconfigure(self._box, image=self._box_images[self._get_look()])

    def _get_look(self) -> str:
        """Red on an error, blue while focused, grey when neither."""
        if self._is_error:
            return "error"

        if self._is_focused:
            return "focused"

        return "normal"

    def _get_box_image(self, border: str) -> tk.PhotoImage:
        return outlined_image(
            self,
            width=self._width,
            height=px(HEIGHT),
            radius=px(RADIUS),
            colour=theme.SURFACE,
            border=border,
            background=self._background,
        )
