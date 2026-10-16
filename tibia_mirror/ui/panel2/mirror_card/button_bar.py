"""The four small buttons of a mirror card: timer, show or hide, lock, remove."""

import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.core.timers import clock
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.mirror_card.icon_button import IconButton
from tibia_mirror.ui.panel2.mirror_card.layout import TOP_ROW_Y
from tibia_mirror.ui.panel2.mirror_card.tip import Tip
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

REMOVE_ICON = "✕"
LOCKED_ICON = "\ue72e"  # a closed lock, from the Segoe MDL2 Assets icon font
UNLOCKED_ICON = "\ue785"  # an open lock, from the same font
SHOWN_ICON = "\ue890"  # an open eye, from the same font
HIDDEN_ICON = "\ued1a"  # a crossed eye, from the same font
TIMER_ICON = "\ue916"  # a clock, from the same font

# Sizes at 100% display scaling; px() scales them where they are used.
RIGHT_PAD = 8  # from the right side of the card to the last button
BUTTON_GAP = 2  # between two buttons


class MirrorCardButtonBar:
    """The buttons at the right of the top row of a mirror card.

    From the right: remove, lock, show or hide, timer. A button in the accent colour
    says that its mirror is in a special state: locked, hidden, or with its timer on.
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        width: int,
        mirror: MirrorInfo,
        on_changed: Callable[[MirrorInfo], None],
    ) -> None:
        self._canvas = canvas
        self._width = width  # of the card
        self._mirror = mirror
        self._on_changed = on_changed  # gets the new info after a button changed the mirror
        self._pressed_button: IconButton | None = None  # the mouse button went down on it

        self._draw_remove_button()
        self._draw_lock_button()
        self._draw_eye_button()
        self._draw_timer_button()
        self._buttons = (
            self._remove_button,
            self._lock_button,
            self._eye_button,
            self._timer_button,
        )

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Show the hover look of the button under the pointer. Return True if there is one."""
        is_over_button: bool = False

        for button in self._buttons:
            is_hovered: bool = button.contains(position_x, position_y)
            button.set_hovered(is_hovered)
            if is_hovered:
                is_over_button = True

        return is_over_button

    def pointer_left(self) -> None:
        """The pointer went out of the card: no button has its hover look."""
        for button in self._buttons:
            button.set_hovered(False)

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Remember the button the mouse button went down on."""
        self._pressed_button = self._get_button_at(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Do what the button does, if the mouse button went down and up on it."""
        button = self._get_button_at(position_x, position_y)
        pressed_button = self._pressed_button
        self._pressed_button = None

        if button is not None and button is pressed_button:
            button.click()

    def set_mirror(self, mirror: MirrorInfo) -> None:
        """Show the buttons for the new state of the mirror."""
        self._mirror = mirror

        icon, colour, hovered_colour = self._get_lock_look()
        self._lock_button.set_look(icon, colour, hovered_colour, self._get_lock_tip())

        icon, colour, hovered_colour = self._get_eye_look()
        self._eye_button.set_look(icon, colour, hovered_colour, self._get_eye_tip())

    def _draw_remove_button(self) -> None:
        tip = Tip(tr("Remove region"))

        self._remove_button = IconButton(
            self._canvas,
            self._get_button_position_x(0),
            px(TOP_ROW_Y),
            REMOVE_ICON,
            theme.FONT,
            theme.SUBTEXT,
            theme.RED,
            tip,
            self._remove,
        )

    def _draw_lock_button(self) -> None:
        """A closed lock in the accent colour for a locked mirror, an open grey lock if not."""
        icon, colour, hovered_colour = self._get_lock_look()

        self._lock_button = IconButton(
            self._canvas,
            self._get_button_position_x(1),
            px(TOP_ROW_Y),
            icon,
            theme.FONT_ICON,
            colour,
            hovered_colour,
            self._get_lock_tip(),
            self._toggle_locked,
        )

    def _get_lock_look(self) -> tuple[str, str, str]:
        """The icon, the colour and the hovered colour of the lock button."""
        if self._mirror.is_locked:
            return LOCKED_ICON, theme.ACCENT, theme.ACCENT
        return UNLOCKED_ICON, theme.SUBTEXT, theme.TEXT

    def _draw_eye_button(self) -> None:
        """A crossed eye in the accent colour for a hidden mirror, an open grey eye if not."""
        icon, colour, hovered_colour = self._get_eye_look()

        self._eye_button = IconButton(
            self._canvas,
            self._get_button_position_x(2),
            px(TOP_ROW_Y),
            icon,
            theme.FONT_ICON,
            colour,
            hovered_colour,
            self._get_eye_tip(),
            self._toggle_hidden,
        )

    def _get_eye_look(self) -> tuple[str, str, str]:
        """The icon, the colour and the hovered colour of the show or hide button."""
        if self._mirror.is_hidden:
            return HIDDEN_ICON, theme.ACCENT, theme.ACCENT
        return SHOWN_ICON, theme.SUBTEXT, theme.TEXT

    def _draw_timer_button(self) -> None:
        """A clock, in the accent colour for a mirror with its timer on, grey if not."""
        is_timer_on: bool = self._mirror.is_timer_on
        colour = theme.ACCENT if is_timer_on else theme.SUBTEXT
        hovered_colour = theme.ACCENT if is_timer_on else theme.TEXT
        tip = self._get_timer_tip()

        self._timer_button = IconButton(
            self._canvas,
            self._get_button_position_x(3),
            px(TOP_ROW_Y),
            TIMER_ICON,
            theme.FONT_ICON,
            colour,
            hovered_colour,
            tip,
            self._open_timer,
        )

    def _get_button_position_x(self, place: int) -> int:
        """The middle of a button. `place` counts the buttons from the right, from 0."""
        size = px(IconButton.SIZE)
        step = size + px(BUTTON_GAP)  # from the middle of one button to the middle of the next
        return self._width - px(RIGHT_PAD) - size // 2 - place * step

    def _get_lock_tip(self) -> Tip:
        """The hint of the lock button. It says what a click does now."""
        if self._mirror.is_locked:
            return Tip(
                tr("Unlock mirror"),
                tr("Lets you move it again. Clicks land on the mirror."),
            )
        return Tip(
            tr("Lock mirror"),
            tr("Pins it in place. Clicks pass through it to the game."),
        )

    def _get_eye_tip(self) -> Tip:
        """The hint of the show or hide button. It says what a click does now."""
        if self._mirror.is_hidden:
            return Tip(tr("Show mirror"))
        return Tip(
            tr("Hide mirror"),
            tr("It stays in the profile; show it again any time."),
        )

    def _get_timer_tip(self) -> Tip:
        """The hint of the timer button. For a timer that is on, it tells the alert time."""
        if self._mirror.is_timer_on:
            time = clock(self._mirror.timer_alert_seconds)
            return Tip(tr("Timer"), tr("On: alerts after {time}.", time=time))
        return Tip(
            tr("Timer"),
            tr("Counts time since you click this region or press its key."),
        )

    def _get_button_at(self, position_x: int, position_y: int) -> IconButton | None:
        """The button at this place, or None."""
        for button in self._buttons:
            if button.contains(position_x, position_y):
                return button

        return None

    def _remove(self) -> None:
        """Remove the mirror from the profile."""

    def _toggle_locked(self) -> None:
        """Lock the mirror in its place, or unlock it."""
        self._on_changed(replace(self._mirror, is_locked=not self._mirror.is_locked))

    def _toggle_hidden(self) -> None:
        """Hide the mirror, or show it again."""
        self._on_changed(replace(self._mirror, is_hidden=not self._mirror.is_hidden))

    def _open_timer(self) -> None:
        """Open the settings of the mirror's timer."""
