"""The Mirrors page: the active profile, the mirrors of that profile, and saving."""

import tkinter as tk

from tibia_mirror.config import DEFAULT_PROFILE
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.profile_picker import ProfilePicker

# Sizes at 100% display scaling; px() scales them where they are used.
TOP_PAD = 18  # above the profile picker
CAPTION_TOP_PAD = 20  # between the profile picker and the caption


class MirrorsPage(tk.Frame):
    """The Mirrors page."""

    def __init__(self, parent: tk.Misc, width: int, side_pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width
        self._side_pad = side_pad
        # add the parts of the page, from top to bottom
        self._add_profile_picker()
        self._add_regions_caption()

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
