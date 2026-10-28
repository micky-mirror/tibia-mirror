"""A key field: a rounded box that shows a key and records a new one."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.timers import KeyCombo
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import icons, theme
from tibia_mirror.ui.base.images import outlined_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import key_combo_name
from tibia_mirror.ui.panel.controls.text_field import HEIGHT, RADIUS, TEXT_PAD

# Sizes at 100% display scaling; px() scales them where they are used.
CLEAR_ICON_INSET = 16  # from the right side of the box to the middle of the ✕


class KeyField(tk.Canvas):
    """A rounded box with a key in it, such as Ctrl+H. A click records a new key."""

    def __init__(
        self,
        parent: tk.Misc,
        key: KeyCombo | None,
        *,
        width: int,
        background: str,
        on_change: Callable[[KeyCombo | None], None],
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=px(HEIGHT),
            bg=background,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._width = width
        self._background = background  # the colour around the box; its round corners blend into it
        self._key = key  # None when no key is set
        self._on_change = on_change  # called with the new key, or None when it is cleared
        self._is_listening = False  # True while the field waits for a key to be pressed
        self._held_modifiers: tuple[str, ...] = ()  # held while listening, such as ("ctrl",)
        # draw key field parts
        self._add_box()
        self._add_text()
        self._add_clear_icon()
        self._update_look()

    def _add_box(self) -> None:
        """The rounded box, with its border in each of its looks."""
        self._box_images = {
            "normal": self._get_box_image(theme.SURFACE_HI),
            "listening": self._get_box_image(theme.ACCENT),
        }
        self._box = self.create_image(0, 0, anchor="nw")

    def _add_text(self) -> None:
        self._text_item = self.create_text(
            px(TEXT_PAD),
            px(HEIGHT) // 2,
            anchor="w",
            font=theme.FONT,
        )

    def _add_clear_icon(self) -> None:
        """The ✕ at the right end of the box. A click on it clears the key."""
        self._clear_icon_item = self.create_text(
            self._width - px(CLEAR_ICON_INSET),
            px(HEIGHT) // 2,
            text=icons.REMOVE,
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )

    def _update_look(self) -> None:
        """Show the box, the text and the ✕ for the current key and state."""
        clear_icon_state = "normal" if self._can_clear() else "hidden"

        self.itemconfigure(self._box, image=self._box_images[self._get_look()])
        self.itemconfigure(self._text_item, text=self._get_text(), fill=self._get_text_colour())
        self.itemconfigure(self._clear_icon_item, state=clear_icon_state)

    def _get_look(self) -> str:
        """Blue while listening, grey when not."""
        if self._is_listening:
            return "listening"

        return "normal"

    def _get_text(self) -> str:
        if self._is_listening:
            return self._get_listening_text()

        if self._key is None:
            return tr("Click to set a key")

        return key_combo_name(self._key)

    def _get_listening_text(self) -> str:
        """The held modifiers, such as "Ctrl+Shift+...", or a request to press a key."""
        if not self._held_modifiers:
            return tr("Press a key...")

        return key_combo_name((None, self._held_modifiers)) + "..."

    def _get_text_colour(self) -> str:
        if self._is_listening:
            return theme.ACCENT

        if self._key is None:
            return theme.SUBTEXT

        return theme.TEXT

    def _can_clear(self) -> bool:
        """True when a key is set and the field is not listening: only then the ✕ shows."""
        return self._key is not None and not self._is_listening

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
