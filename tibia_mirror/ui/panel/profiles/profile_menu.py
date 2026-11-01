"""The menu of the profile picker: the profiles, and what can be done with them."""

import tkinter as tk
from collections.abc import Callable, Sequence
from functools import partial

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.core.geometry import Box
from tibia_mirror.core.mirrors.regions import next_default_name
from tibia_mirror.core.profiles.profile_names import copy_name, name_error
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.text import key_combo_name
from tibia_mirror.ui.panel.controls.confirm_dialog import ConfirmDialog
from tibia_mirror.ui.panel.controls.dropdown_menu import DIVIDER, DropdownMenu, MenuOption
from tibia_mirror.ui.panel.controls.name_dialog import NameDialog
from tibia_mirror.ui.panel.profiles.profile_key_dialog import ProfileKeyDialog

# The keys of the actions in the menu. The other keys are profile names, and
# a profile name can't hold "<" or ">", so the two never mix.
NEW = "<new>"
DUPLICATE = "<duplicate>"
RENAME = "<rename>"
KEY = "<key>"
DELETE = "<delete>"


class ProfileMenu:
    """The menu that opens under the profile picker.

    It lists every profile, with a check mark at the active one, and then the
    things that can be done with profiles.
    """

    def __init__(
        self,
        window: tk.Misc,
        profile_manager: ProfileManager,
        active_name: str,
        profile_names: Sequence[str],
        on_select: Callable[[str], None],
        on_new: Callable[[str], None],
        on_duplicate: Callable[[str], None],
        on_rename: Callable[[str], None],
        on_delete: Callable[[], None],
    ) -> None:
        self._window = window  # the main window, the menu and its dialogs open over it
        self._profile_manager = profile_manager  # gets and sets the profile keys
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
        menu = DropdownMenu(self._window, self._get_options(), self._active_name, self._on_pick)
        menu.open(box, on_close)

    def _get_options(self) -> list[MenuOption | None]:
        """Every profile with its key, then what can be done with profiles.

        The last profile can't be deleted.
        """
        options: list[MenuOption | None] = [
            *[
                MenuOption(name, name, side_text=self._get_key_name(name))
                for name in self._profile_names
            ],
            DIVIDER,
            MenuOption(NEW, tr("New profile…")),
            MenuOption(DUPLICATE, tr("Duplicate…")),
            MenuOption(RENAME, tr("Rename…")),
            MenuOption(KEY, tr("Add key…"), text_colour=theme.ACCENT),
        ]

        if len(self._profile_names) > 1:
            options += [DIVIDER, MenuOption(DELETE, tr("Delete profile"), text_colour=theme.RED)]

        return options

    def _get_key_name(self, name: str) -> str | None:
        """The key that opens the profile `name`, such as "Ctrl+F5". None if it has no key."""
        key = self._profile_manager.get_key(name)

        return None if key is None else key_combo_name(key)

    def _on_pick(self, key: str) -> None:
        """Do what the picked option stands for: an action, or opening a profile."""
        actions = {
            NEW: self._new,
            DUPLICATE: self._duplicate,
            RENAME: self._rename,
            KEY: self._set_key,
            DELETE: self._delete,
        }

        if key in actions:
            actions[key]()
        else:
            self._select(key)

    def _select(self, name: str) -> None:
        """Make the profile `name` the active one. Do nothing when it is already active."""
        if name == self._active_name:
            return

        self._on_select(name)

    def _new(self) -> None:
        """Ask for a name and make a new, empty profile."""
        suggested_name = next_default_name(self._profile_names, stem=tr("Profile"))

        NameDialog(
            self._window,
            tr("New profile"),
            suggested_name,
            on_ok=self._on_new,
            on_cancel=lambda: None,
            get_name_error=partial(name_error, taken=self._profile_names),
        )

    def _duplicate(self) -> None:
        """Ask for a name and make a copy of the active profile."""
        suggested_name = copy_name(self._active_name, self._profile_names, tr("copy"))

        NameDialog(
            self._window,
            tr("Duplicate profile"),
            suggested_name,
            on_ok=self._on_duplicate,
            on_cancel=lambda: None,
            get_name_error=partial(name_error, taken=self._profile_names),
        )

    def _rename(self) -> None:
        """Ask for a new name for the active profile."""
        other_names = [name for name in self._profile_names if name != self._active_name]

        NameDialog(
            self._window,
            tr("Rename profile"),
            self._active_name,
            on_ok=self._on_rename,
            on_cancel=lambda: None,
            get_name_error=partial(name_error, taken=other_names),
        )

    def _set_key(self) -> None:
        """Ask for the key that opens the active profile."""
        ProfileKeyDialog(
            self._window,
            self._active_name,
            self._profile_manager.get_key(self._active_name),
            on_ok=self._profile_manager.set_key,
        )

    def _delete(self) -> None:
        """Ask if the user is sure, then delete the active profile."""
        message = tr(
            'Delete "{name}" and all its mirrors? This can\'t be undone.',
            name=self._active_name,
        )
        ConfirmDialog(
            self._window,
            tr("Delete profile"),
            message,
            tr("Delete"),
            on_ok=self._on_delete,
            on_cancel=lambda: None,
            is_danger=True,
        )
