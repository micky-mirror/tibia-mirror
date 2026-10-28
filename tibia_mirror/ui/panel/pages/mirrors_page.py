"""The Mirrors page: the active profile and the mirrors of that profile."""

import tkinter as tk
from collections.abc import Callable, Sequence
from functools import partial

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.raised_button import RaisedButton
from tibia_mirror.ui.panel.controls.scroll_list import ScrollList
from tibia_mirror.ui.panel.mirrors.mirror_card.card import MirrorCard
from tibia_mirror.ui.panel.mirrors.mirror_info import MirrorInfo
from tibia_mirror.ui.panel.profiles.profile_info import ProfileInfo
from tibia_mirror.ui.panel.profiles.profile_picker import ProfilePicker

# Sizes at 100% display scaling; px() scales them where they are used.
TOP_PAD = 18  # above the profile picker
CAPTION_TOP_PAD = 20  # between the profile picker and the caption
CAPTION_BOTTOM_PAD = 7  # between the caption and the Add region button
ADD_BUTTON_HEIGHT = 42
LIST_TOP_PAD = 2  # between the shadow of the Add region button and the list
LIST_BOTTOM_PAD = 8  # below the list
HINT_TOP_PAD = 10  # above the sentence that shows in place of the cards
CARD_GAP = 6  # under each mirror card


class MirrorsPage(tk.Frame):
    """The Mirrors page."""

    def __init__(
        self,
        parent: tk.Misc,
        width: int,
        side_pad: int,
        profile_info: ProfileInfo,
        on_profile_selected: Callable[[str], None],
        on_new_profile: Callable[[str], None],
        on_duplicate_profile: Callable[[str], None],
        on_rename_profile: Callable[[str], None],
        on_delete_profile: Callable[[], None],
        mirrors: Sequence[MirrorInfo] | None,
        on_mirror_changed: Callable[[MirrorInfo], None],
        on_mirror_removed: Callable[[str], None],
        on_select_area: Callable[[str | None], None],
    ) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width
        self._side_pad = side_pad
        self._profile_info = profile_info
        self._on_profile_selected = on_profile_selected  # gets the name picked in the menu
        self._on_new_profile = on_new_profile  # gets the name typed for a new profile
        self._on_duplicate_profile = on_duplicate_profile  # gets the name typed for the copy
        self._on_rename_profile = on_rename_profile  # gets the new name typed for the profile
        self._on_delete_profile = on_delete_profile  # called when the user confirms the delete
        self._mirrors = mirrors  # None while Tibia is not connected
        self._on_mirror_changed = on_mirror_changed  # gets the new info after a card changed it
        self._on_mirror_removed = on_mirror_removed  # gets the mirror id after a card removed it
        # gets the id of the mirror whose area is selected again, None for a new mirror
        self._on_select_area = on_select_area
        # add the parts of the page, from top to bottom
        self._add_profile_picker()
        self._add_regions_caption()
        self._add_region_button()
        self._add_mirror_list()
        self._show_mirrors()

    def _add_profile_picker(self) -> None:
        """The box at the top with the name of the active profile."""
        self._profile_picker = ProfilePicker(
            self,
            self._width,
            self._profile_info.active_name,
            self._profile_info.names,
            self._on_profile_selected,
            self._on_new_profile,
            self._on_duplicate_profile,
            self._on_rename_profile,
            self._on_delete_profile,
        )
        self._profile_picker.pack(
            side="top",
            anchor="w",
            padx=self._side_pad,
            pady=(px(TOP_PAD), 0),
        )

    def _add_regions_caption(self) -> None:
        """The small grey title above the Add region button and the list of mirrors."""
        caption = tk.Label(
            self,
            text=tr("REGIONS"),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_CAPTION,
        )
        caption.pack(
            side="top",
            anchor="w",
            padx=self._side_pad,
            pady=(px(CAPTION_TOP_PAD), 0),
        )

    def _add_region_button(self) -> None:
        """The big button that starts the adding of a new mirror."""
        button = RaisedButton(
            self,
            "+  " + tr("Add region"),
            partial(self._on_select_area, None),
            width=self._width,
            height=px(ADD_BUTTON_HEIGHT),
            style=theme.PRIMARY_BUTTON,
            hover_fill=theme.ACCENT_HI,
            font=theme.FONT_BUTTON,
            text_colour=theme.ON_ACCENT,
            background=theme.BG,
        )
        # The widget is bigger than the button we see: it has room for the shadow around it.
        # The spaces are made smaller by that room, so the button itself lands in line.
        shadow = button.margins
        button.pack(
            side="top",
            anchor="w",
            padx=(self._side_pad - shadow.left, 0),
            pady=(max(0, px(CAPTION_BOTTOM_PAD) - shadow.top), 0),
        )

    def _add_mirror_list(self) -> None:
        """The list of the mirrors. It scrolls when they do not fit."""
        scroll_list = ScrollList(self, width=self._width)
        scroll_list.pack(
            side="top",
            anchor="w",
            fill="y",
            expand=True,
            padx=(self._side_pad, 0),
            pady=(px(LIST_TOP_PAD), px(LIST_BOTTOM_PAD)),
        )
        self._mirror_list = scroll_list.inner

    def set_profile_info(self, profile_info: ProfileInfo) -> None:
        """Show another active profile in the profile picker."""
        self._profile_info = profile_info
        self._profile_picker.set_profile(profile_info.active_name, profile_info.names)

    def set_mirrors(self, mirrors: Sequence[MirrorInfo] | None) -> None:
        """Show these mirrors in place of the ones shown before. Do nothing when nothing changed."""
        if mirrors == self._mirrors:
            return

        self._mirrors = mirrors
        self._redraw_mirror_list()

    def _redraw_mirror_list(self) -> None:
        """Draw the cards, or the sentence, again from the page's list of mirrors."""
        self._clear_mirror_list()
        self._show_mirrors()

    def _clear_mirror_list(self) -> None:
        """Remove every card, or the sentence, from the list."""
        for child in self._mirror_list.winfo_children():
            child.destroy()

    def _show_mirrors(self) -> None:
        """Fill the list: a card for each mirror, or a sentence when there is nothing to show."""
        if self._mirrors is None:
            hint = tr("This profile's mirrors appear once Tibia is connected.")
            self._add_hint(hint)
            return

        if not self._mirrors:
            hint = tr("Click Add region, then drag a box over the part of the game to mirror.")
            self._add_hint(hint)
            return

        for mirror in self._mirrors:
            card = MirrorCard(
                self._mirror_list,
                self._width,
                mirror,
                self._on_card_changed,
                self._on_card_removed,
                self._on_select_area,
                self._on_card_renamed,
            )
            card.pack(side="top", anchor="w", pady=(0, px(CARD_GAP)))

    def _on_card_changed(self, changed_mirror: MirrorInfo) -> None:
        """Put a change made on a card into the list of the page, and pass it on."""
        if self._mirrors is not None:
            self._mirrors = [
                changed_mirror if mirror.mirror_id == changed_mirror.mirror_id else mirror
                for mirror in self._mirrors
            ]

        self._on_mirror_changed(changed_mirror)

    def _on_card_renamed(self, renamed_mirror: MirrorInfo) -> None:
        """Keep and pass on the new name, then draw the cards again: the size moves with it."""
        self._on_card_changed(renamed_mirror)
        # The card is still handling the click, so it cannot be destroyed yet.
        self.after_idle(self._redraw_mirror_list)

    def _on_card_removed(self, mirror_id: str) -> None:
        """Take the mirror of a card out of the list of the page, and pass it on."""
        if self._mirrors is not None:
            self._mirrors = [mirror for mirror in self._mirrors if mirror.mirror_id != mirror_id]

        self._on_mirror_removed(mirror_id)
        # The card is still handling the click, so it cannot be destroyed yet.
        # after_idle draws the list again when the card has finished.
        self.after_idle(self._redraw_mirror_list)

    def _add_hint(self, text: str) -> None:
        """A grey sentence in the list, in place of the cards."""
        hint = tk.Label(
            self._mirror_list,
            text=text,
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT,
            justify="left",
            wraplength=self._width,
        )
        hint.pack(side="top", anchor="w", pady=(px(HINT_TOP_PAD), 0))
