"""The menu of the profile picker: the profiles, and what can be done with them."""

import tkinter as tk
from collections.abc import Callable, Sequence
from functools import partial

from tibia_mirror.core.geometry import Box, Point
from tibia_mirror.core.profiles import copy_name, name_error
from tibia_mirror.core.regions import next_default_name
from tibia_mirror.i18n import tr
from tibia_mirror.ui.panel.controls.dialogs import Choice, ChoiceDialog, NameDialog
from tibia_mirror.ui.panel.controls.menu import SEPARATOR, MenuItem, PopupMenu


class ProfileMenu:
    """The menu that opens under the profile picker.

    It lists every profile, with a check mark at the active one, and then the
    things that can be done with profiles.
    """

    def __init__(
        self,
        window: tk.Misc,
        active_name: str,
        profile_names: Sequence[str],
        on_select: Callable[[str], None],
        on_new: Callable[[str], None],
        on_duplicate: Callable[[str], None],
        on_rename: Callable[[str], None],
        on_delete: Callable[[], None],
    ) -> None:
        self._window = window  # the main window, the menu and its dialogs open over it
        self._active_name = active_name  # the name of the active profile
        self._profile_names = profile_names  # the names of all profiles
        self._on_select = on_select  # gets the name of the profile picked in the menu
        self._on_new = on_new  # gets the name typed for a new profile
        self._on_duplicate = on_duplicate  # gets the name typed for the copy
        self._on_rename = on_rename  # gets the new name typed for the active profile
        self._on_delete = on_delete  # called when the user confirms the delete

    def open(self, box: Box, on_close: Callable[[], None]) -> None:
        """Open the menu under `box`, as wide as it. `box` is a place on the screen.

        `on_close` is called when the menu closes.
        """
        PopupMenu(self._window, box, self._get_items(), on_close=on_close)

    def _get_items(self) -> list[MenuItem | None]:
        """The entries of the menu: every profile, then what can be done with profiles."""
        # the last profile cannot be deleted
        has_other_profiles: bool = len(self._profile_names) > 1
        return [
            *self._get_profile_items(),
            SEPARATOR,
            MenuItem(tr("New profile…"), self._new),
            MenuItem(tr("Duplicate…"), self._duplicate),
            MenuItem(tr("Rename…"), self._rename),
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
        default_name = next_default_name(self._profile_names, stem=tr("Profile"))
        center = self._get_window_center()

        NameDialog(
            self._window,
            default_name,
            center,
            on_ok=self._on_new,
            on_cancel=lambda: None,
            title=tr("New profile"),
            validate=partial(name_error, taken=self._profile_names),
        )

    def _duplicate(self) -> None:
        """Ask for a name and make a copy of the active profile."""
        default_name = copy_name(self._active_name, self._profile_names, tr("copy"))
        center = self._get_window_center()

        NameDialog(
            self._window,
            default_name,
            center,
            on_ok=self._on_duplicate,
            on_cancel=lambda: None,
            title=tr("Duplicate profile"),
            validate=partial(name_error, taken=self._profile_names),
        )

    def _rename(self) -> None:
        """Ask for a new name for the active profile."""
        other_names = [name for name in self._profile_names if name != self._active_name]
        center = self._get_window_center()

        NameDialog(
            self._window,
            self._active_name,
            center,
            on_ok=self._on_rename,
            on_cancel=lambda: None,
            title=tr("Rename profile"),
            validate=partial(name_error, taken=other_names),
        )

    def _delete(self) -> None:
        """Ask if the user is sure, then delete the active profile."""
        message = tr(
            'Delete "{name}" and all its mirrors? This can\'t be undone.',
            name=self._active_name,
        )
        center = self._get_window_center()
        choices = [
            Choice(tr("Cancel"), lambda: None),
            Choice(tr("Delete"), self._on_delete, "danger"),
        ]

        ChoiceDialog(self._window, tr("Delete profile"), message, center, choices)

    def _get_window_center(self) -> Point:
        """The middle of the main window on the screen, where the dialogs open."""
        center_x = self._window.winfo_rootx() + self._window.winfo_width() // 2
        center_y = self._window.winfo_rooty() + self._window.winfo_height() // 2

        return center_x, center_y
