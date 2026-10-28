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
from tibia_mirror.winapi import win32

# Sizes at 100% display scaling; px() scales them where they are used.
CLEAR_ICON_INSET = 16  # from the right side of the box to the middle of the ✕
CLEAR_AREA = 28  # a click this close to the right side of the box clears the key

# Tk's names of the modifier keys. Pressed alone, they only show in the text.
MODIFIER_KEYSYMS = frozenset(
    {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L", "Meta_R"}
)


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
        self._bind_events()

    def set_key(self, key: KeyCombo | None) -> None:
        """Show another key, after it was changed somewhere else."""
        self._key = key
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

    def _bind_events(self) -> None:
        self.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.bind("<KeyPress>", self._on_key_down)
        self.bind("<KeyRelease>", self._on_key_up)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        is_on_clear_area = event.x >= self._width - px(CLEAR_AREA)

        if self._can_clear() and is_on_clear_area:
            self._change_key(None)
        else:
            self._start_listening()

    def _on_key_down(self, event: tk.Event[tk.Canvas]) -> str | None:
        if not self._is_listening:
            return None

        if event.keysym in MODIFIER_KEYSYMS:
            self._update_held_modifiers()
            return "break"

        self._stop_listening()
        if event.keysym != "Escape":
            # Tk on Windows gives the virtual-key code as the keycode.
            self._change_key((event.keycode, win32.modifiers_down()))

        return "break"  # keeps the dialog's Enter and Escape out of it

    def _on_key_up(self, event: tk.Event[tk.Canvas]) -> None:
        if self._is_listening and event.keysym in MODIFIER_KEYSYMS:
            self._update_held_modifiers()

    def _on_focus_out(self, event: tk.Event[tk.Canvas]) -> None:
        self._stop_listening()

    def _start_listening(self) -> None:
        self._is_listening = True
        self._held_modifiers = ()
        self.focus_set()
        self._update_look()

    def _stop_listening(self) -> None:
        self._is_listening = False
        self._update_look()

    def _update_held_modifiers(self) -> None:
        self._held_modifiers = win32.modifiers_down()
        self._update_look()

    def _change_key(self, key: KeyCombo | None) -> None:
        self.set_key(key)
        self._on_change(key)

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
