"""The menu of the profile picker: the profiles, and what can be done with them."""

import tkinter as tk
from collections.abc import Callable, Sequence
from functools import partial

from tibia_mirror.core.geometry import Box
from tibia_mirror.i18n import tr
from tibia_mirror.ui.controls.menu import SEPARATOR, MenuItem, PopupMenu


class ProfileMenu:
    """The menu that opens under the profile picker.

    It lists every profile, with a check mark at the active one, and then the
    things that can be done with profiles.
    """

    def __init__(
        self,
        active_name: str,
        profile_names: Sequence[str],
        on_select: Callable[[str], None],
    ) -> None:
        self._active_name = active_name  # the name of the active profile
        self._profile_names = profile_names  # the names of all profiles
        self._on_select = on_select  # gets the name of the profile picked in the menu

    def open(self, window: tk.Misc, box: Box, on_close: Callable[[], None]) -> None:
        """Open the menu under `box`, as wide as it. `box` is a place on the screen.

        `on_close` is called when the menu closes.
        """
        PopupMenu(window, box, self._get_items(), on_close=on_close)

    def _get_items(self) -> list[MenuItem | None]:
        """The entries of the menu: every profile, then what can be done with profiles."""
        # two entries need a second profile: there is nothing to copy from, and the last
        # profile cannot be deleted
        has_other_profiles: bool = len(self._profile_names) > 1
        return [
            *self._get_profile_items(),
            SEPARATOR,
            MenuItem(tr("New profile…"), self._new),
            MenuItem(tr("Duplicate…"), self._duplicate),
            MenuItem(tr("Rename…"), self._rename),
            SEPARATOR,
            MenuItem(tr("Characters…"), self._characters),
            MenuItem(tr("Copy from…"), self._copy_from, enabled=has_other_profiles),
            SEPARATOR,
            MenuItem(tr("Import…"), self._import),
            MenuItem(tr("Export…"), self._export),
            SEPARATOR,
            MenuItem(tr("Delete profile"), self._delete, enabled=has_other_profiles, danger=True),
        ]

    def _get_profile_items(self) -> list[MenuItem]:
        """One entry for each profile, with a check mark at the active one."""
        return [
            MenuItem(name, partial(self._select, name), checked=name == self._active_name)
            for name in self._profile_names
        ]

    def _select(self, name: str) -> None:
        """Make the profile `name` the active one. Do nothing when it is already active."""
        if name == self._active_name:
            return

        self._on_select(name)

    def _new(self) -> None:
        """Ask for a name and make a new, empty profile."""

    def _duplicate(self) -> None:
        """Ask for a name and make a copy of the active profile."""

    def _rename(self) -> None:
        """Ask for a new name for the active profile."""

    def _characters(self) -> None:
        """Let the user choose which characters open the active profile when they log in."""

    def _copy_from(self) -> None:
        """Ask for another profile and copy its mirrors into the active one."""

    def _import(self) -> None:
        """Ask for a profile file and add it as a new profile."""

    def _export(self) -> None:
        """Ask where to save, and write the active profile to a file."""

    def _delete(self) -> None:
        """Ask if the user is sure, then delete the active profile."""
