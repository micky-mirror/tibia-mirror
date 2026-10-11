"""The Mirrors page: the active profile, the mirrors of that profile, and saving."""

import tkinter as tk

from tibia_mirror.config import DEFAULT_PROFILE
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.render import margins
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import RaisedButton
from tibia_mirror.ui.panel2.profile_picker import ProfilePicker

# Sizes at 100% display scaling; px() scales them where they are used.
TOP_PAD = 18  # above the profile picker
CAPTION_TOP_PAD = 20  # between the profile picker and the caption
CAPTION_BOTTOM_PAD = 7  # between the caption and the Add region button
ADD_BUTTON_HEIGHT = 42
SAVE_BUTTON_HEIGHT = 34
SAVE_BUTTON_GAP = 12  # between the Save button and the Revert button
BOTTOM_PAD = 14  # below the line that tells if the changes are saved


class MirrorsPage(tk.Frame):
    """The Mirrors page."""

    def __init__(self, parent: tk.Misc, width: int, side_pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width
        self._side_pad = side_pad
        # add the parts of the page, from top to bottom
        self._add_profile_picker()
        self._add_regions_caption()
        self._add_region_button()
        # add the parts at the bottom of the page, from the bottom up
        self._add_save_state()
        self._add_save_buttons()

    def _add_profile_picker(self) -> None:
        """The box at the top with the name of the active profile."""
        profile_picker = ProfilePicker(self, self._width, DEFAULT_PROFILE, [DEFAULT_PROFILE])
        profile_picker.pack(
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
            self._on_add_region,
            width=self._width,
            height=px(ADD_BUTTON_HEIGHT),
            style=theme.PRIMARY_BUTTON,
            hover_fill=theme.ACCENT_HI,
            font=theme.FONT_BUTTON,
            fg=theme.ON_ACCENT,
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

    def _on_add_region(self) -> None:
        """Let the user drag a box over the part of the game that the new mirror will show."""

    def _add_save_state(self) -> None:
        """The line at the bottom that tells if the changes are saved."""
        save_state = tk.Label(
            self,
            text=tr("All changes saved"),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT,
        )
        save_state.pack(
            side="bottom",
            anchor="w",
            padx=self._side_pad,
            pady=(0, px(BOTTOM_PAD)),
        )

    def _add_save_buttons(self) -> None:
        """The Save and Revert buttons, side by side above the save state line.

        Each one is half as wide as the content. They are grey while there is nothing to save.
        """
        # A button's widget has room for its shadow around the button we see. Two widgets
        # cannot lie on top of each other, so the gap is at least as wide as both rooms.
        shadow = margins(theme.SAVE_BUTTON)
        gap = max(px(SAVE_BUTTON_GAP), shadow.right + shadow.left)
        button_width = (self._width - gap) // 2

        row = tk.Frame(self, bg=theme.BG)
        row.pack(side="bottom", anchor="w", padx=(self._side_pad - shadow.left, 0))

        save = RaisedButton(
            row,
            tr("Save"),
            self._on_save,
            width=button_width,
            height=px(SAVE_BUTTON_HEIGHT),
            style=theme.SAVE_BUTTON,
            hover_fill=theme.GREEN_HI,
            font=theme.FONT_BOLD,
            fg=theme.ON_ACCENT,
            background=theme.BG,
        )
        save.set_enabled(False)
        save.pack(side="left")

    def _on_save(self) -> None:
        """Save the mirrors of the active profile."""
