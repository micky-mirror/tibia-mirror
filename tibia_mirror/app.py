"""The App: owns the runtime state (Tibia, mirrors, profiles, settings) and wires it together."""

from __future__ import annotations

import time
from functools import partial

from tibia_mirror import errors, i18n
from tibia_mirror.app_parts.app_window import AppWindow
from tibia_mirror.app_parts.mirror_manager import MirrorManager
from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.app_parts.settings_writer import SettingsWriter
from tibia_mirror.app_parts.tibia_connection import TibiaConnection
from tibia_mirror.app_parts.timer_manager import TimerManager
from tibia_mirror.config import (
    APP_ID,
    ERROR_LOG,
    ERROR_LOG_MAX_BYTES,
    PROFILES_DIR,
    SETTINGS_FILE,
    TIMER_TICK_MS,
)
from tibia_mirror.core import regions
from tibia_mirror.core.connection import MINIMIZED
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.profile import Profile
from tibia_mirror.core.timers import combo_matches
from tibia_mirror.i18n import tr, tr_n
from tibia_mirror.settings.app_settings import AppSettings
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.overlay.selection_overlay import NewRegionOverlay, SelectionOverlay
from tibia_mirror.ui.panel.controls.dialogs import key_combo_name
from tibia_mirror.ui.panel.panel import Panel
from tibia_mirror.ui.panel.profiles.profile_info import ProfileInfo
from tibia_mirror.winapi import win32
from tibia_mirror.winapi.instance import SingleInstance
from tibia_mirror.winapi.rawinput import InputWatcher


class App:
    """The app: starts its parts and connects them."""

    def __init__(self, instance: SingleInstance) -> None:
        # Read settings.json. A missing or broken file gives the default settings.
        self.settings = AppSettingsStore(SETTINGS_FILE, self._on_settings_changed)
        self.window = AppWindow(self.settings, instance)
        # the panel that shows the message is built later, so it is looked up on a failure
        self.settings_writer = SettingsWriter(
            self.window,
            self.settings,
            on_failed=lambda: self.panel.set_message(tr("Save failed"), "error"),
        )
        self.connection = TibiaConnection(
            self.window,
            self._on_connection_changed,
            self._on_game_window_changed,
            self._on_character_changed,
        )
        self.profile_manager = ProfileManager(PROFILES_DIR, self.settings, self._on_profile_changed)
        self.timer_manager = TimerManager(self.settings, self.profile_manager, self.connection)
        self.mirror_manager = MirrorManager(
            self.window, self.settings, self.profile_manager, self.timer_manager, self.connection
        )
        self._is_all_hidden = False  # True while the hide-all key keeps every mirror hidden
        # hear the keys and clicks of the whole computer, to act on those meant for Tibia
        self.input_watcher = InputWatcher(self._on_click, self._on_key)
        self.input_watcher.start(self.window)
        # use the saved language for every text
        i18n.use(self.settings.current.language)
        self._show_panel()
        # check if the profile was loaded from its file
        is_profile_loaded = self._load_profile()
        self.window.show()

        if not is_profile_loaded:
            self.panel.set_message(tr("Profile file is invalid"), "error")
        else:
            self._show_mirrors()

        # open the profile of a character who was logged in before the app started
        self._on_character_changed(self.connection.character)
        # show the time of the timers on their badges
        self._tick_timers()

    def run(self) -> None:
        self.window.mainloop()

    def _on_settings_changed(self, previous: AppSettings, current: AppSettings) -> None:
        """Save the settings on a delay, and make the app follow the settings that changed."""
        self.settings_writer.write_on_delay()

        if current.is_panel_on_top != previous.is_panel_on_top:
            self.window.set_panel_on_top()

        if current.is_profile_per_character_on and not previous.is_profile_per_character_on:
            self._on_character_changed(self.connection.character)

        if current.hide_all_key != previous.hide_all_key:
            self._follow_hide_all_key()

        is_mirror_look_changed = (
            current.is_mirror_frame_on != previous.is_mirror_frame_on
            or current.is_rounded_corners_on != previous.is_rounded_corners_on
            or current.is_frame_tint_on != previous.is_frame_tint_on
        )

        if is_mirror_look_changed:
            self.mirror_manager.update_mirror_look()

    def _on_connection_changed(self, state: str) -> None:
        """Show the new state of the connection on the panel, and show or close the mirrors."""
        self.panel.set_connection_state(state)
        self._show_mirrors()

    def _on_game_window_changed(self, game_window: GameWindow) -> None:
        """Make the mirrors follow the window of Tibia after it changed."""
        self.mirror_manager.set_game_window(game_window)
        self.panel.set_mirrors(self.mirror_manager.get_mirror_infos())

    def _on_character_changed(self, character: str | None) -> None:
        """Pause the timers at a logout, and continue them from their saved spots at a login.

        A character who logged in gets their profile, when Profile per character is on.
        """
        now = time.monotonic()
        self.timer_manager.pause_timers(now)

        if character is not None and self.settings.current.is_profile_per_character_on:
            self._open_character_profile(character)

        self.timer_manager.continue_timers(now)

    def _open_character_profile(self, character: str) -> None:
        """Open the profile with the character's name, or make one from the open profile."""
        name = self.profile_manager.find_name(character)

        if name is None:
            self._on_duplicate_profile(character)
        elif name != self.profile_manager.active_name:
            self._on_profile_selected(name)

    def _on_click(self, button: str, position_x: int, position_y: int, pressed_at: float) -> None:
        """Start the timers of the mirrors whose area was clicked in Tibia."""
        game_window = self.connection.game_window

        if button != "left" or game_window is None:
            return

        # only clicks that Tibia gets count, not clicks on a window above it
        if win32.toplevel_at(position_x, position_y) != game_window.handle:
            return

        self.timer_manager.start_by_click(game_window, position_x, position_y, pressed_at)

    def _on_key(self, key_code: int, modifiers: tuple[str, ...]) -> None:
        """Act on a key pressed in Tibia: the hide-all key, or the key of a timer."""
        game_window = self.connection.game_window
        hide_all_key = self.settings.current.hide_all_key

        # only keys pressed while Tibia has the focus count, not keys typed in the panel
        if game_window is None or win32.foreground_window() != game_window.handle:
            return

        if combo_matches(hide_all_key, key_code, modifiers):
            self._toggle_all_hidden()
            return

        self.timer_manager.start_by_key(key_code, modifiers, time.monotonic())

    # It plans its next run first, so an error in one run cannot stop it for good.
    def _tick_timers(self) -> None:
        """Show the time of every timer on its badge, again every TIMER_TICK_MS."""
        self.window.after(TIMER_TICK_MS, self._tick_timers)
        self.mirror_manager.update_timer_badges(time.monotonic())

    def _toggle_all_hidden(self) -> None:
        """Hide all mirrors, or bring them back."""
        self._is_all_hidden = not self._is_all_hidden
        self._show_mirrors()
        self._show_hidden_note()

    def _show_hidden_note(self) -> None:
        """Say on the panel if the hide-all key hides the mirrors, and which key it is."""
        hide_all_key = self.settings.current.hide_all_key

        if not self._is_all_hidden or hide_all_key is None:
            self.panel.set_all_hidden(None)
        else:
            self.panel.set_all_hidden(key_combo_name(hide_all_key))

    def _follow_hide_all_key(self) -> None:
        """Bring the mirrors back when the key is cleared, else name the new key in the note."""
        if self.settings.current.hide_all_key is None and self._is_all_hidden:
            # no key is left to bring the mirrors back
            self._toggle_all_hidden()
        else:
            self._show_hidden_note()

    def _on_profile_changed(self, previous: Profile, current: Profile) -> None:
        """Save the open profile after it changed.

        The mirror windows and the Mirrors page follow the change.
        """
        try:
            self.profile_manager.save()
        except OSError:
            self.panel.set_message(tr("Save failed"), "error")

        self.mirror_manager.update_windows()
        self.panel.set_mirrors(self.mirror_manager.get_mirror_infos())

    def _on_profile_selected(self, name: str) -> None:
        """Open another profile, and show its mirrors. Every timer stops."""
        self.profile_manager.open(name)
        self.timer_manager.stop_all()
        self.panel.set_profile_info(self._get_profile_info())

        if self._load_profile():
            self.panel.set_message("")
        else:
            self.panel.set_message(tr("Profile file is invalid"), "error")

        self._show_mirrors()

    def _on_new_profile(self, name: str) -> None:
        """Create an empty profile with the name typed in the menu, and open it."""
        try:
            self.profile_manager.write_mirrors(name, [])
        except OSError:
            self.panel.set_message(tr("Could not create profile"), "error")
        else:
            self._on_profile_selected(name)

    def _on_duplicate_profile(self, name: str) -> None:
        """Copy the open profile under a new name, and open the copy."""
        try:
            self.profile_manager.duplicate(name)
        except OSError:
            self.panel.set_message(tr("Could not duplicate profile"), "error")
        else:
            self._on_profile_selected(name)

    def _on_rename_profile(self, name: str) -> None:
        """Give the open profile the name typed in the menu, and show it in the picker."""
        try:
            self.profile_manager.rename(name)
        except OSError:
            self.panel.set_message(tr("Could not rename profile"), "error")
        else:
            self.panel.set_profile_info(self._get_profile_info())

    def _on_delete_profile(self) -> None:
        """Delete the open profile, and show the profile opened in its place."""
        try:
            self.profile_manager.delete()
        except OSError:
            self.panel.set_message(tr("Could not delete profile"), "error")
        else:
            self._on_profile_selected(self.profile_manager.active_name)

    def _on_select_area(self, mirror_id: str | None) -> None:
        game_window = self.connection.game_window

        if game_window is None:
            is_minimized = self.connection.state == MINIMIZED
            message = tr("Restore Tibia first") if is_minimized else tr("Start Tibia first")
            self.panel.set_message(message, "error")
            return

        # the mirrors would cover the game while the user selects a part of it
        self.mirror_manager.close()
        on_selected = partial(self._on_area_selected, mirror_id)

        if mirror_id is not None:
            SelectionOverlay(self.window, game_window, on_selected, self._show_mirrors)
            return

        names = [mirror_settings.name for mirror_settings in self.profile_manager.current.mirrors]
        suggested_name = regions.next_default_name(names, stem=tr("Region"))
        NewRegionOverlay(
            self.window,
            game_window,
            suggested_name,
            on_selected,
            self._show_mirrors,
        )

    def _on_area_selected(self, mirror_id: str | None, area: Rect, name: str = "") -> None:
        if self.connection.game_window is None:
            # Tibia closed while the user was selecting or naming
            self.panel.set_message(tr("Could not mirror"), "error")
            return

        if mirror_id is None:
            self.mirror_manager.add_mirror(name, area)
        else:
            self.mirror_manager.set_area(mirror_id, area)

        self._show_mirrors()

    def _load_profile(self) -> bool:
        """Read the open profile. False if its file is invalid."""
        try:
            self.profile_manager.load()
        except (OSError, ValueError):
            return False
        else:
            return True

    def _show_mirrors(self) -> None:
        """Show the kept mirrors on the Mirrors page and on the window of Tibia.

        The windows close without a window of Tibia, and while the hide-all key hides them.
        """
        self.panel.set_mirrors(self.mirror_manager.get_mirror_infos())

        if self._is_all_hidden:
            self.mirror_manager.close()
            return

        failed = self.mirror_manager.show()
        # new windows show the time of a counting timer at once, not on the next tick
        self.mirror_manager.update_timer_badges(time.monotonic())

        if failed:
            message = tr_n(failed, "{n} mirror failed to load", "{n} mirrors failed to load")
            self.panel.set_message(message, "error")

    def _get_profile_info(self) -> ProfileInfo:
        """What the profile picker shows: the open profile and the names of all profiles."""
        return ProfileInfo(
            active_name=self.profile_manager.active_name,
            names=tuple(self.profile_manager.get_names()),
        )

    def _show_panel(self) -> None:
        profile_info = self._get_profile_info()
        mirror_infos = self.mirror_manager.get_mirror_infos()

        self.panel = Panel(
            self.window,
            self.settings,
            self.profile_manager,
            self.connection.state,
            profile_info,
            self._on_profile_selected,
            self._on_new_profile,
            self._on_duplicate_profile,
            self._on_rename_profile,
            self._on_delete_profile,
            mirror_infos,
            self.mirror_manager.update_mirror,
            self.profile_manager.remove_mirror,
            self._on_select_area,
        )
        self.panel.pack(fill="both", expand=True)
        self._show_hidden_note()


def main() -> None:
    # Everything up to the panel showing: a failure here gets a message box,
    # since the app would otherwise just never appear.
    try:
        # Before anything touches the data folder: a second copy only brings
        # the first one's panel to the front, and quits.
        instance = SingleInstance(APP_ID)
        if not instance.first:
            instance.ask_first_to_show()
            return
        errors.start(ERROR_LOG, ERROR_LOG_MAX_BYTES)
        app = App(instance)
    except Exception as e:
        errors.log_exception(type(e), e, e.__traceback__)
        win32.error_box(
            "Tibia Mirror",
            tr("Tibia Mirror couldn't start. The details are in:\n{path}", path=ERROR_LOG),
        )
        raise SystemExit(1) from e
    app.run()
