"""The App: owns the runtime state (Tibia, mirrors, profiles, settings) and wires it together."""

from __future__ import annotations

import os
import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog
from types import TracebackType
from typing import Any

from tibia_mirror import errors, i18n
from tibia_mirror.config import (
    APP_ID,
    ATTACH_POLL_MS,
    AUTOSAVE_DELAY_MS,
    ERROR_LOG,
    ERROR_LOG_MAX_BYTES,
    FADE_MS,
    ICON_FILE,
    MIN_SELECTION_SIDE,
    NEW_MIRROR_GAP,
    PANEL_FRAME,
    PANEL_MIN_SIZE,
    PANEL_SIZE,
    PROFILES_DIR,
    SETTINGS_FILE,
    SETTINGS_SAVE_DELAY_MS,
    TIMER_TICK_MS,
    VISIBILITY_POLL_MS,
    ZOOM_RANGE,
)
from tibia_mirror.core import characters, regions, settings
from tibia_mirror.core.characters import Links
from tibia_mirror.core.geometry import Point, Rect, fit_panel_size, panel_geometry, place_beside
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.core.profiles import ProfileStore, copy_name, name_error
from tibia_mirror.core.settings import PanelRect
from tibia_mirror.core.timers import (
    KeyCombo,
    Pauses,
    TimerSettings,
    button_matches,
    combo_matches,
    key_clashes,
    key_matches,
    pauses_of,
    with_pauses,
    without_mirrors,
)
from tibia_mirror.core.visibility import mirrors_should_show, next_last_external
from tibia_mirror.i18n import tr, tr_n
from tibia_mirror.services.active_profile import LOAD_ERRORS, ActiveProfile
from tibia_mirror.services.game import Game
from tibia_mirror.services.mirrors import Mirrors
from tibia_mirror.ui.base import scale, theme
from tibia_mirror.ui.controls.dialogs import (
    CharactersDialog,
    Choice,
    ChoiceDialog,
    CopyFromDialog,
    NameDialog,
    RegionDialog,
    TimerDialog,
    key_combo_name,
)
from tibia_mirror.ui.overlay.mirror import MirrorLook, MirrorWindow
from tibia_mirror.ui.overlay.selector import RegionSelector
from tibia_mirror.ui.panel.mirrors_page import (
    MirrorsActions,
    ProfileActions,
    RegionActions,
    region_count,
)
from tibia_mirror.ui.panel.panel import ControlPanel
from tibia_mirror.ui.panel.settings_page import SettingValue
from tibia_mirror.winapi import dwm, sounds, win32
from tibia_mirror.winapi.instance import SingleInstance
from tibia_mirror.winapi.rawinput import InputWatcher


def _nothing() -> None:
    pass


class _Root(tk.Tk):
    """The panel's window, sending errors in Tk callbacks to the error log."""

    def report_callback_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        errors.log_exception(exc_type, exc_value, exc_traceback)


class App:
    def __init__(
        self,
        instance: SingleInstance,
        profiles_dir: Path = PROFILES_DIR,
        settings_file: Path = SETTINGS_FILE,
    ) -> None:
        win32.enable_dpi_awareness()
        win32.set_app_id(APP_ID)
        self._instance = instance
        self.store = ProfileStore(profiles_dir)
        self.store.ensure_one()
        self.settings_file = settings_file
        self.settings = settings.load(settings_file)
        names = self.store.names()
        # Windows file names ignore case, so match the remembered profile the same way.
        self.profile = ActiveProfile(
            self.store,
            next(
                (name for name in names if name.casefold() == self.settings.profile.casefold()),
                names[0],
            ),
        )
        self.game = Game()
        self._pid = os.getpid()
        self._last_external: Hwnd | None = None  # last foreground window not owned by this app
        self._character: str | None = None  # logged in to Tibia, from its window title
        # Like _character, but updated at once (a profile switch may wait), so
        # timers that pause while logged out lose no time.
        self._online: str | None = None
        # Whose paused timers show while logged out; remembered for the next start.
        self._last_online: str | None = self.settings.last_character or None
        # Mirror id -> start time of _online's pausing timers, across profiles. Lost
        # if the app closes while logged in: online time after that is unknown.
        self._running: dict[str, float] = {}
        self._selecting = False
        # Hidden with the hide-all key; each mirror keeps its own hidden flag too.
        # Not remembered across starts.
        self._all_hidden = False
        # Tk `after` job ids of the pending debounced saves (see _schedule).
        self._autosave_job: str | None = None
        self._settings_job: str | None = None
        self._selector: RegionSelector | None = None
        # Clicks and key presses from anywhere: used only for timers and the hide-all key.
        self._input = InputWatcher(self._on_click, self._on_key)

        self.root = _Root()
        # Pixel sizes follow the display scaling from here on, as the fonts do.
        scale.init(self.root)
        theme.use(self.settings.theme)
        i18n.use(self.settings.language)
        self.root.title("Tibia Mirror")
        # -default: every window of the app gets it, the dialogs too. Called
        # through tk.call because tkinter's stubs leave iconbitmap() untyped.
        self.root.tk.call("wm", "iconbitmap", str(self.root), "-default", str(ICON_FILE))
        self.root.minsize(scale.px(PANEL_MIN_SIZE[0]), scale.px(PANEL_MIN_SIZE[1]))
        self._panel_area = self._place_panel()
        self.root.configure(bg=theme.BG)
        self.root.attributes("-topmost", self.settings.panel_on_top)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.mirrors = Mirrors(
            self.root, on_remove=self.remove_mirror, on_changed=lambda _mirror: self._changed()
        )
        self._panel_actions = MirrorsActions(
            add=self.add_region,
            save=self.save,
            revert=self.revert,
            region=RegionActions(
                remove=self.remove_mirror,
                hover=self.highlight_mirror,
                set_opacity=self.set_mirror_opacity,
                adjust=self.set_mirror_adjusting,
                rename=self.rename_mirror,
                resize=self.resize_mirror,
                set_hidden=self.set_mirror_hidden,
                set_locked=self.set_mirror_locked,
                set_color=self.set_mirror_color,
                timer=self.edit_mirror_timer,
            ),
            profile=ProfileActions(
                select=self.select_profile,
                new=self.new_profile,
                duplicate=self.duplicate_profile,
                rename=self.rename_profile,
                characters=self.edit_characters,
                copy_from=self.copy_profile_from,
                delete=self.delete_profile,
                import_file=self.import_profile,
                export_file=self.export_profile,
            ),
        )
        self._build_panel()
        self.panel_hwnd = win32.toplevel_hwnd(self.root)
        dwm.set_dark_title_bar(self.panel_hwnd, self.settings.theme == "dark")
        self._keep_panel_on_screen()
        # Every widget carries the root in its bindtags: _panel_moved filters by widget.
        self.root.bind("<Configure>", self._panel_moved, add="+")

    # ---- the panel's place --------------------------------------------------
    def _place_panel(self) -> Rect:
        """Where the panel was last, shrunk to fit; centred the first time.

        Returns the work area it was placed on, for _keep_panel_on_screen.
        """
        min_size = (scale.px(PANEL_MIN_SIZE[0]), scale.px(PANEL_MIN_SIZE[1]))
        frame = scale.px(PANEL_FRAME)
        saved = self.settings.panel_rect
        if saved is None:
            area = win32.work_area_at((0, 0))
            size = (scale.px(PANEL_SIZE[0]), scale.px(PANEL_SIZE[1]))
            self.root.geometry(panel_geometry(size, min_size[1], frame, area))
            return area
        x, y, width, height = saved
        area = win32.work_area_at((x + width // 2, y + height // 2))
        width, height = fit_panel_size((width, height), min_size, frame, area)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        return area

    def _keep_panel_on_screen(self) -> None:
        """Centre the panel if what it shows (title bar and inside) isn't fully on its screen,
        e.g. after a monitor was unplugged. Its invisible resize borders may stick out.
        """
        client = win32.client_rect(self.panel_hwnd)
        top = self.root.winfo_y()  # the title bar's top: no invisible border there
        shown = Rect(client.x, top, client.w, client.bottom - top)
        if not self._panel_area.contains_rect(shown):
            min_height, frame = scale.px(PANEL_MIN_SIZE[1]), scale.px(PANEL_FRAME)
            size = (client.w, client.h)
            self.root.geometry(panel_geometry(size, min_height, frame, self._panel_area))

    def _panel_moved(self, e: tk.Event[tk.Misc]) -> None:
        """Remember the panel's place and size, to open there next time (not while
        minimized or maximized: it reopens where it was before)."""
        if e.widget is not self.root or self.root.state() != "normal":
            return
        rect = (self.root.winfo_x(), self.root.winfo_y(), e.width, e.height)
        if rect != self.settings.panel_rect:
            self._update_settings(panel_rect=rect)

    def run(self) -> None:
        self._input.start(self.root)
        self._attach_poll()
        self._visibility_poll()
        self._timer_poll()
        self.root.mainloop()

    def close(self) -> None:
        def quit_app() -> None:
            if self._settings_job is not None:
                self._cancel("_settings_job")
                self._save_settings()
            self._input.stop()
            self.root.destroy()

        self._resolve_unsaved(
            tr('Save changes to "{name}" before closing?', name=self.profile.name), quit_app
        )

    # ---- mirrors page actions -----------------------------------------------
    def add_region(self) -> None:
        connected = self._require_client()
        if connected is not None:
            self._select_region(connected[0], self._on_region_selected)

    def save(self, quiet: bool = False) -> bool:
        """Write the mirrors to the active profile; returns whether that worked."""
        self._cancel("_autosave_job")
        try:
            self.profile.save(mirror.to_saved() for mirror in self.mirrors)
        except OSError:
            self.page.set_status(tr("Save failed"), "error")
            return False
        self._changed()
        if not quiet:
            self.page.set_status(
                tr("Saved {regions}", regions=region_count(len(self.mirrors))), "ok"
            )
        return True

    def revert(self) -> None:
        if self._require_client() is not None:
            self._load_mirrors()

    # ---- region card actions ------------------------------------------------
    def remove_mirror(self, mirror: MirrorWindow) -> None:
        self.mirrors.remove(mirror)
        self._forget_timer(mirror)
        self._show_regions()
        self._changed()

    def highlight_mirror(self, mirror: MirrorWindow, hovered: bool) -> None:
        if mirror in self.mirrors:
            mirror.set_highlighted(hovered)

    def set_mirror_opacity(self, mirror: MirrorWindow, value: float) -> None:
        if mirror in self.mirrors:
            mirror.set_opacity(value)
            self._changed()

    def set_mirror_adjusting(self, mirror: MirrorWindow, adjusting: bool) -> None:
        if mirror in self.mirrors:
            mirror.set_adjusting(adjusting)

    def set_mirror_hidden(self, mirror: MirrorWindow, hidden: bool) -> None:
        if mirror in self.mirrors:
            mirror.set_hidden(hidden)
            self._changed()

    def set_mirror_locked(self, mirror: MirrorWindow, locked: bool) -> None:
        if mirror in self.mirrors:
            mirror.set_locked(locked)
            self._changed()

    def edit_mirror_timer(self, mirror: MirrorWindow, center: Point) -> None:
        if mirror in self.mirrors:
            TimerDialog(
                self.root,
                mirror.name,
                mirror.timer,
                center,
                on_ok=lambda settings: self._set_mirror_timer(mirror, settings),
                on_cancel=_nothing,
                reserved=self.settings.hide_all_combo,
            )

    def _set_mirror_timer(self, mirror: MirrorWindow, settings: TimerSettings) -> None:
        if mirror in self.mirrors and settings != mirror.timer:
            mirror.set_timer(settings)  # starts over, so any progress is gone
            self._forget_timer(mirror)
            self._sync_timer(mirror, time.monotonic())
            self._show_regions()  # the card's clock icon shows whether it is on
            self._changed()

    def set_mirror_color(self, mirror: MirrorWindow, color: str) -> None:
        if mirror in self.mirrors:
            mirror.set_color(color)
            self._show_regions()  # the card's dot shows the colour
            self._changed()

    def rename_mirror(self, mirror: MirrorWindow, center: Point) -> None:
        if mirror not in self.mirrors:
            return
        NameDialog(
            self.root,
            mirror.name,
            center,
            on_ok=lambda name: self._rename_mirror(mirror, name),
            on_cancel=_nothing,
            title=tr("Rename region"),
        )

    def resize_mirror(self, mirror: MirrorWindow, center: Point) -> None:
        """Open the region dialog; edits preview live and only stick on OK."""
        if mirror not in self.mirrors:
            return
        connected = self._require_client()
        if connected is None:
            return
        _game_hwnd, client = connected
        original = (mirror.rect, mirror.zoom)

        def finish() -> None:
            mirror.set_editing(False)

        def cancel() -> None:
            mirror.preview(*original)  # restores without saving a guessed layout
            finish()

        def ok(rect: Rect, zoom: float, apply_to_all: bool) -> None:
            finish()
            self._apply_region(mirror, rect, zoom, apply_to_all)

        def reselect() -> None:
            cancel()
            self._reselect_region(mirror)

        mirror.set_editing(True)
        RegionDialog(
            self.root,
            mirror.name,
            mirror.rect,
            mirror.zoom,
            (client.w, client.h),
            MIN_SELECTION_SIDE,
            ZOOM_RANGE,
            center,
            on_preview=mirror.preview,
            on_ok=ok,
            on_reselect=reselect,
            on_cancel=cancel,
            can_apply_to_all=len(self.mirrors) > 1,
        )

    # ---- profile actions ----------------------------------------------------
    def select_profile(self, name: str) -> None:
        if name != self.profile.name:
            self._resolve_unsaved(
                tr('Save changes to "{name}" before switching?', name=self.profile.name),
                lambda: self._open_profile(name),
            )

    def new_profile(self) -> None:
        names = self.store.names()
        NameDialog(
            self.root,
            regions.next_default_name(names, stem=tr("Profile")),
            self._panel_center(),
            on_ok=lambda name: self._resolve_unsaved(
                tr('Save changes to "{name}" before switching?', name=self.profile.name),
                lambda: self._create_profile(name),
            ),
            on_cancel=_nothing,
            title=tr("New profile"),
            validate=lambda name: name_error(name, names),
        )

    def duplicate_profile(self) -> None:
        names = self.store.names()
        NameDialog(
            self.root,
            copy_name(self.profile.name, names, tr("copy")),
            self._panel_center(),
            on_ok=self._duplicate_profile,
            on_cancel=_nothing,
            title=tr("Duplicate profile"),
            validate=lambda name: name_error(name, names),
        )

    def rename_profile(self) -> None:
        others = [name for name in self.store.names() if name != self.profile.name]
        NameDialog(
            self.root,
            self.profile.name,
            self._panel_center(),
            on_ok=self._rename_profile,
            on_cancel=_nothing,
            title=tr("Rename profile"),
            validate=lambda name: name_error(name, others),
        )

    def import_profile(self) -> None:
        chosen = filedialog.askopenfilename(
            parent=self.root,
            title=tr("Import profile"),
            filetypes=[(tr("Tibia Mirror profile"), "*.json"), (tr("All files"), "*.*")],
        )
        if not chosen:
            return
        path = Path(chosen)
        # Files from before layouts need the game's client area to be read.
        client = self.game.current_client() if self.game.hwnd is not None else None
        try:
            saved = regions.load(path, client)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self.page.set_status(tr("Not a readable profile file"), "error")
            return
        names = self.store.names()
        default = (
            path.stem
            if name_error(path.stem, names) is None
            else copy_name(path.stem, names, tr("copy"))
        )
        NameDialog(
            self.root,
            default,
            self._panel_center(),
            on_ok=lambda name: self._resolve_unsaved(
                tr('Save changes to "{name}" before switching?', name=self.profile.name),
                lambda: self._import_profile(name, saved),
            ),
            on_cancel=_nothing,
            title=tr("Import profile"),
            validate=lambda name: name_error(name, names),
        )

    def export_profile(self) -> None:
        """Save the active profile, as last saved, to a file of the user's choice."""
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title=tr("Export profile"),
            initialfile=f"{self.profile.name}.json",
            defaultextension=".json",
            filetypes=[(tr("Tibia Mirror profile"), "*.json")],
        )
        if not path:
            return
        try:
            self.store.export(self.profile.name, Path(path))
        except OSError:
            self.page.set_status(tr("Export failed"), "error")
            return
        self.page.set_status(tr('Exported "{name}"', name=self.profile.name), "ok")

    def edit_characters(self) -> None:
        CharactersDialog(
            self.root,
            self.profile.name,
            self.settings.characters,
            self._panel_center(),
            on_change=self._set_links,
        )

    def copy_profile_from(self) -> None:
        sources = [name for name in self.store.names() if name != self.profile.name]
        if sources and self._require_client() is not None:
            CopyFromDialog(
                self.root, self.profile.name, sources, self._panel_center(), self._copy_mirrors_from
            )

    def delete_profile(self) -> None:
        if len(self.store.names()) < 2:
            return
        ChoiceDialog(
            self.root,
            tr("Delete profile"),
            tr(
                'Delete "{name}" and all its mirrors? This can\'t be undone.',
                name=self.profile.name,
            ),
            self._panel_center(),
            [
                Choice(tr("Cancel"), _nothing),
                Choice(tr("Delete"), self._delete_profile, "danger"),
            ],
        )

    # ---- settings -----------------------------------------------------------
    def set_setting(self, key: str, value: SettingValue) -> str | None:
        """Apply a changed setting; returns why the hide-all key was refused, or None."""
        if key == "hide_all":
            return self._set_hide_all_key(value if isinstance(value, tuple) else None)
        self._update_settings(**{key: value})
        # Read back from the settings, where each value has its own type.
        if key == "autosave":
            self.page.set_autosave(self.settings.autosave)
            self._changed()
        elif key in ("mirror_frame", "fades", "rounded_corners", "frame_tint"):
            self.mirrors.set_look(self._look())
        elif key == "panel_on_top":
            self.root.attributes("-topmost", self.settings.panel_on_top)
        elif key in ("theme", "language"):
            # After the click that chose it has finished with the old widgets.
            self.root.after_idle(self._restyle)
        elif key == "profile_per_character" and self.settings.profile_per_character:
            if self._character is not None:
                self._open_character_profile(self._character)
        return None

    def _set_hide_all_key(self, combo: KeyCombo | None) -> str | None:
        clash = None if combo is None else self._timer_using(combo)
        if combo is not None and clash is not None:
            name, profile = clash
            key_name = key_combo_name(combo)
            if profile == self.profile.name:
                return tr('{key} already starts the timer of "{name}".', key=key_name, name=name)
            return tr(
                '{key} already starts the timer of "{name}" in profile "{profile}".',
                key=key_name,
                name=name,
                profile=profile,
            )
        vk, modifiers = combo or (None, ())
        self._update_settings(hide_all_key=vk, hide_all_modifiers=modifiers)
        if combo is None and self._all_hidden:
            self._toggle_all_hidden()  # no key left to bring them back
        else:
            self._show_all_hidden()
        return None

    def _timer_using(self, combo: KeyCombo) -> tuple[str, str] | None:
        """(mirror name, profile) of an enabled timer that `combo` starts, or None."""

        def timers(profile: str) -> list[tuple[str, TimerSettings]]:
            if profile == self.profile.name and not self.profile.needs_load:
                return [(mirror.name, mirror.timer) for mirror in self.mirrors]
            return [(e.name, e.timer) for e in self.store.load(profile, self.game.client)]

        for profile in [
            self.profile.name,
            *(name for name in self.store.names() if name != self.profile.name),
        ]:
            try:
                found = [name for name, timer in timers(profile) if key_clashes(timer, combo)]
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                continue  # an unreadable profile starts no timers
            if found:
                return found[0], profile
        return None

    def _toggle_all_hidden(self) -> None:
        self._all_hidden = not self._all_hidden
        self._apply_visibility()
        self._show_all_hidden()

    def _show_all_hidden(self) -> None:
        combo = self.settings.hide_all_combo
        self.panel.set_all_hidden(
            key_combo_name(combo) if self._all_hidden and combo is not None else None
        )

    # ---- internals ----------------------------------------------------------
    def _build_panel(self, page: str = "mirrors") -> None:
        """Build the panel in the current theme and fill it from the App's state."""
        self.panel = ControlPanel(
            self.root, self.settings, self._panel_actions, self.set_setting, page=page
        )
        self.page = self.panel.mirrors
        self.page.set_profiles(self.store.names(), self.profile.name)
        self.page.set_autosave(self.settings.autosave)
        self._show_regions()
        self._show_connection()
        self._show_all_hidden()
        self.page.set_unsaved(self._unsaved())

    def _restyle(self) -> None:
        """Apply the theme and language settings: rebuild the panel on the same page."""
        theme.use(self.settings.theme)
        i18n.use(self.settings.language)
        self.root.configure(bg=theme.BG)
        dwm.set_dark_title_bar(self.panel_hwnd, self.settings.theme == "dark")
        page = self.panel.page
        self.panel.destroy()
        self._build_panel(page)
        self.mirrors.set_look(self._look())  # the mirror frame colour comes from the theme

    def _require_game(self) -> Hwnd | None:
        """Tibia's window, or None after telling the user to start it."""
        if self.game.hwnd is None:
            self.page.set_status(tr("Start Tibia first"), "error")
        return self.game.hwnd

    def _require_client(self) -> tuple[Hwnd, Rect] | None:
        """Tibia's window and client area, or None after telling the user what's missing."""
        game_hwnd = self._require_game()
        if game_hwnd is None:
            return None
        client = self.game.current_client()
        if client is None:
            self.page.set_status(tr("Restore Tibia first"), "error")
            return None
        return game_hwnd, client

    def _panel_center(self) -> Point:
        root = self.root
        return (
            root.winfo_rootx() + root.winfo_width() // 2,
            root.winfo_rooty() + root.winfo_height() // 2,
        )

    def _look(self) -> MirrorLook:
        return MirrorLook(
            frame=self.settings.mirror_frame,
            fade_ms=FADE_MS if self.settings.fades else 0,
            rounded=self.settings.rounded_corners,
            tint=self.settings.frame_tint,
        )

    def _schedule(self, attr: str, delay_ms: int, callback: Callable[[], object]) -> None:
        """Run callback after delay_ms, replacing whatever job `attr` holds (a debounce)."""
        self._cancel(attr)

        def run() -> None:
            setattr(self, attr, None)
            callback()

        setattr(self, attr, self.root.after(delay_ms, run))

    def _cancel(self, attr: str) -> None:
        job: str | None = getattr(self, attr)
        if job is not None:
            self.root.after_cancel(job)
            setattr(self, attr, None)

    def _update_settings(
        self, **changes: SettingValue | tuple[str, ...] | Links | Pauses | PanelRect
    ) -> None:
        # replace() checks the names; each value's type is the caller's to get right.
        fields: dict[str, Any] = changes
        self.settings = replace(self.settings, **fields)
        self._schedule("_settings_job", SETTINGS_SAVE_DELAY_MS, self._save_settings)

    def _save_settings(self) -> None:
        try:
            settings.save(self.settings_file, self.settings)
        except OSError:
            self.page.set_status(tr("Could not save settings"), "error")

    def _unsaved(self) -> bool:
        return self.profile.has_unsaved(mirror.to_saved() for mirror in self.mirrors)

    def _changed(self) -> None:
        """Call after anything that may change what Save would write."""
        unsaved = self._unsaved()
        self.page.set_unsaved(unsaved)
        if unsaved and self.settings.autosave:
            self._schedule("_autosave_job", AUTOSAVE_DELAY_MS, lambda: self.save(quiet=True))

    def _resolve_unsaved(self, question: str, then: Callable[[], None]) -> None:
        """Run `then` once unsaved changes are saved or discarded.

        With auto-save on they are saved silently; otherwise the user chooses.
        """
        if not self._unsaved() or (self.settings.autosave and self.save(quiet=True)):
            then()
            return

        def save_then() -> None:
            if self.save():
                then()

        ChoiceDialog(
            self.root,
            tr("Unsaved changes"),
            question,
            self._panel_center(),
            [
                Choice(tr("Cancel"), _nothing),
                Choice(tr("Discard"), then),
                Choice(tr("Save"), save_then, "primary"),
            ],
        )

    def _set_active_profile(self, name: str) -> None:
        self.profile.name = name
        self.page.set_profiles(self.store.names(), name)
        self._update_settings(profile=name)

    def _open_profile(self, name: str) -> None:
        """Make `name` the active profile and show its mirrors (once Tibia is connected)."""
        self._cancel("_autosave_job")
        self._set_active_profile(name)
        if self.game.hwnd is not None and self.game.client is not None:
            self._load_mirrors()
            return
        # Loaded by _attach_poll once Tibia is running and not minimized.
        self.mirrors.clear()
        self.profile.needs_load = True
        self.profile.mark_saved([])
        self._show_regions()
        self._changed()

    def _create_profile(self, name: str) -> None:
        try:
            self.store.save(name, [])
        except OSError:
            self.page.set_status(tr("Could not create profile"), "error")
            return
        self._open_profile(name)

    def _duplicate_profile(self, name: str) -> None:
        """Save what is on screen (unsaved changes included) as a new profile and switch to it."""
        loaded = not self.profile.needs_load
        saved = [mirror.to_saved() for mirror in self.mirrors]
        try:
            if loaded:
                self.store.save(name, saved)
            else:
                # Until Tibia connects the mirrors are not loaded yet, so copy the file.
                self.store.copy(self.profile.name, name)
        except OSError:
            self.page.set_status(tr("Could not duplicate profile"), "error")
            return
        self._cancel("_autosave_job")
        if loaded:
            self.profile.mark_saved(saved)
        self._set_active_profile(name)
        self._changed()

    def _import_profile(self, name: str, saved: list[regions.SavedRegion]) -> None:
        try:
            self.store.save(name, saved)
        except OSError:
            self.page.set_status(tr("Could not import profile"), "error")
            return
        self._open_profile(name)

    def _rename_profile(self, name: str) -> None:
        old_name = self.profile.name
        if name == old_name:
            return
        try:
            self.profile.rename(name)
        except OSError:
            self.page.set_status(tr("Could not rename profile"), "error")
            return
        self._set_links(characters.rename_profile(self.settings.characters, old_name, name))
        self._set_active_profile(name)

    def _delete_profile(self) -> None:
        self._cancel("_autosave_job")
        try:
            self.profile.delete()
        except OSError:
            self.page.set_status(tr("Could not delete profile"), "error")
            return
        self._set_links(characters.drop_profile(self.settings.characters, self.profile.name))
        self._open_profile(self.store.names()[0])

    def _set_links(self, links: Links) -> None:
        self._update_settings(characters=links)

    def _copy_mirrors_from(self, source: str) -> None:
        """Replace the mirrors on screen with `source`'s as saved, as an unsaved change."""
        if self._require_client() is None or self.profile.needs_load:
            return
        try:
            saved = self.store.load(source, self.game.current_client())
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self.page.set_status(tr("Profile file is invalid"), "error")
            return
        self.mirrors.clear()
        failed = sum(not self._create_mirror(e) for e in saved)
        self._show_regions()
        if failed:
            self.page.set_status(
                tr_n(failed, "{n} mirror failed to load", "{n} mirrors failed to load"), "error"
            )
        else:
            self.page.set_status(
                tr('Copied {regions} from "{name}"', regions=region_count(len(saved)), name=source),
                "ok",
            )
        self._changed()
        self._apply_visibility()

    def _check_character(self) -> None:
        """Notice a character logging in: open its profile, if that setting is on."""
        character = characters.character_in_title(self.game.title())
        if character != self._online:
            self._timers_online(character)
        if character == self._character:
            return
        wanted = character is not None and self.settings.profile_per_character
        # Switching would pull the mirrors from under a selection or an open
        # dialog, so it waits for them; the login is only noted once handled.
        if wanted and (self._selecting or self._dialog_open()):
            return
        self._character = character
        if character is not None and wanted:
            self._open_character_profile(character)

    # ---- timers that pause while logged out ---------------------------------
    def _timers_online(self, character: str | None) -> None:
        """A character logged in or out (None): pause or continue its timers."""
        now = time.monotonic()
        pauses = self.settings.timer_pauses
        if self._online is not None:
            elapsed = {mirror_id: now - start for mirror_id, start in self._running.items()}
            pauses = with_pauses(pauses, self._online, elapsed)
            self._last_online = self._online
        self._online = character
        self._running = {}
        if character is not None:
            # Running again: kept in memory until the logout, see _running.
            self._running = {
                mirror_id: now - seconds
                for mirror_id, seconds in pauses_of(pauses, character).items()
            }
            pauses = with_pauses(pauses, character, {})
        if pauses != self.settings.timer_pauses:
            self._update_settings(timer_pauses=pauses)
        if (self._last_online or "") != self.settings.last_character:
            self._update_settings(last_character=self._last_online or "")
        for mirror in self.mirrors:
            self._sync_timer(mirror, now)

    def _sync_timer(self, mirror: MirrorWindow, now: float) -> None:
        """Show a pausing timer's state for who is logged in, or as paused at the last logout."""
        if not mirror.timer.pauses_offline:
            return
        if self._online is not None:
            mirror.restore_timer(now, started=self._running.get(mirror.id))
        elif self._last_online is not None:
            paused = pauses_of(self.settings.timer_pauses, self._last_online).get(mirror.id)
            mirror.restore_timer(now, paused=paused)
        else:
            mirror.restore_timer(now)

    def _start_timer(self, mirror: MirrorWindow, at: float) -> None:
        if mirror.timer.pauses_offline:
            if self._online is None:
                return  # it only counts while a character is logged in
            self._running[mirror.id] = at
        mirror.start_timer(at)

    def _forget_timer(self, mirror: MirrorWindow) -> None:
        """Drop a timer's progress, for every character: it was removed or set up anew."""
        self._running.pop(mirror.id, None)
        pauses = without_mirrors(self.settings.timer_pauses, {mirror.id})
        if pauses != self.settings.timer_pauses:
            self._update_settings(timer_pauses=pauses)

    def _dialog_open(self) -> bool:
        """Whether a modal dialog holds the grab.

        Via tk.call, since tkinter's stubs leave grab_current() untyped.
        """
        return bool(self.root.tk.call("grab", "current"))

    def _open_character_profile(self, character: str) -> None:
        """Open the character's profile; on its first login, link it to one first.

        That's an unused profile with its name, or a new copy of the active profile.
        Unsaved changes are resolved first, as when switching by hand.
        """
        names = self.store.names()
        links = self.settings.characters
        linked = characters.profile_of(links, character)
        target = next(
            (name for name in names if linked and name.casefold() == linked.casefold()), None
        )
        question = tr('Save changes to "{name}" before switching?', name=self.profile.name)
        if target is not None:
            if target != self.profile.name:
                self._resolve_unsaved(question, lambda: self._open_for(character, target))
            return
        name, exists = characters.profile_for_new_character(character, names, links, tr("copy"))

        def create() -> None:
            if not exists:
                try:
                    self.store.copy(self.profile.name, name)
                except OSError:
                    self.page.set_status(tr("Could not create profile"), "error")
                    return
            self._set_links(characters.link(self.settings.characters, character, name))
            self._open_for(character, name, created=not exists)

        if exists and name == self.profile.name:
            create()
        else:
            self._resolve_unsaved(question, create)

    def _open_for(self, character: str, name: str, created: bool = False) -> None:
        if name != self.profile.name:
            self._open_profile(name)
        # The picker above shows the profile's name.
        if created:
            status = tr("Created for {character}", character=character)
        else:
            status = tr("Opened for {character}", character=character)
        self.page.set_status(status, "ok")

    def _load_mirrors(self) -> None:
        """Replace the mirrors with the active profile as saved on disk."""
        self._cancel("_autosave_job")
        self.mirrors.clear()
        try:
            saved = self.profile.load(self.game.current_client())
        except LOAD_ERRORS:
            self._show_regions()
            self.page.set_status(tr("Profile file is invalid"), "error")
            self._changed()
            return
        failed = sum(not self._create_mirror(e) for e in saved)
        self._show_regions()
        if failed:
            self.page.set_status(
                tr_n(failed, "{n} mirror failed to load", "{n} mirrors failed to load"), "error"
            )
        self._changed()
        self._apply_visibility()

    def _select_region(self, game_hwnd: Hwnd, on_done: Callable[[Rect], None]) -> None:
        """Let the user drag out part of the game: on_done(rect in client coordinates).

        Tibia is never brought to the front, so the part must already be in view.
        """
        self._selecting = True
        self._apply_visibility()
        self._selector = RegionSelector(self.root, game_hwnd, on_done, self._selection_cancelled)

    def _reselect_region(self, mirror: MirrorWindow) -> None:
        def done(rect: Rect) -> None:
            self._end_selection()
            if mirror in self.mirrors:
                mirror.set_region(rect)
                self._show_regions()
                self._changed()
            self._return_to_panel()

        connected = self._require_client()
        if connected is not None:
            self._select_region(connected[0], done)

    def _apply_region(
        self, mirror: MirrorWindow, rect: Rect, zoom: float, apply_to_all: bool
    ) -> None:
        """Keep the dialog's result; with apply_to_all the others take its size and zoom."""
        if mirror in self.mirrors:
            mirror.set_region(rect)
            mirror.set_zoom(zoom)
        if apply_to_all:
            for other in self.mirrors:
                if other is not mirror:
                    other.resize_region(rect.w, rect.h)  # around each one's own centre
                    other.set_zoom(zoom)
        self._show_regions()
        self._changed()

    def _track_client(self) -> None:
        """Keep mirrors on the game's client area as it moves or changes size."""
        change = self.game.track_client()
        if change is None:
            return
        client, resized = change
        self.mirrors.set_client(client)
        if resized:
            self._show_regions()  # the cards show region sizes

    def _end_selection(self) -> None:
        self._selecting = False
        self._apply_visibility()

    def _selection_cancelled(self) -> None:
        self._end_selection()
        self._return_to_panel()

    def _return_to_panel(self) -> None:
        """Bring the panel back after adding a region; closing the overlay leaves focus anywhere."""
        win32.bring_to_front(self.panel_hwnd)

    def _on_region_selected(self, rect: Rect) -> None:
        self._end_selection()
        if self.game.hwnd is None:
            return  # Tibia closed; closing it already cancels a selection
        client_x, client_y = win32.client_origin(self.game.hwnd)
        on_screen = Rect(client_x + rect.x, client_y + rect.y, rect.w, rect.h)
        center = (on_screen.x + on_screen.w // 2, on_screen.y + on_screen.h // 2)
        NameDialog(
            self.root,
            regions.next_default_name((mirror.name for mirror in self.mirrors), stem=tr("Region")),
            center,
            on_ok=lambda name: self._add_named_region(name, rect, on_screen),
            on_cancel=self._return_to_panel,
        )

    def _rename_mirror(self, mirror: MirrorWindow, name: str) -> None:
        if mirror not in self.mirrors or name == mirror.name:
            return
        mirror.name = name
        self._show_regions()
        self._changed()

    def _add_named_region(self, name: str, rect: Rect, on_screen: Rect) -> None:
        # New mirrors start at actual size (zoom 1).
        center = (on_screen.x + on_screen.w // 2, on_screen.y + on_screen.h // 2)
        bounds = win32.work_area_at(center)
        x, y = place_beside(on_screen, rect.w, rect.h, bounds, scale.px(NEW_MIRROR_GAP))
        client = self.game.current_client()
        if client is None:  # Tibia was minimized or closed while the name was typed
            self.page.set_status(tr("Could not mirror"), "error")
            self._return_to_panel()
            return
        layout = regions.Layout(rect, (x - client.x, y - client.y))
        ok = self._create_mirror(
            regions.SavedRegion(
                name,
                {regions.size_key(client.w, client.h): layout},
                self.settings.new_opacity,
            )
        )
        self._show_regions()
        if not ok:
            self.page.set_status(tr("Could not mirror"), "error")
        self._changed()
        self._apply_visibility()
        self._return_to_panel()

    def _create_mirror(self, saved: regions.SavedRegion) -> bool:
        """Show a mirror of `saved`; False if there is no game to mirror or DWM refuses."""
        game_hwnd, client = self.game.hwnd, self.game.client
        if game_hwnd is None or client is None:
            return False
        mirror = self.mirrors.add(saved, game_hwnd, client, self._look())
        if mirror is None:
            return False
        self._sync_timer(mirror, time.monotonic())
        return True

    def _attach_poll(self) -> None:
        game_hwnd = self.game.find()
        if game_hwnd is None:
            self.root.after(ATTACH_POLL_MS, self._attach_poll)
            return
        # Mirrors are laid out on the game's client area, which a minimized
        # Tibia does not have: wait until it is restored.
        client = self.game.current_client()
        if client is None:
            self._show_connection()
            self._show_regions()
            self.root.after(ATTACH_POLL_MS, self._attach_poll)
            return
        self._show_connection()
        if self.profile.needs_load:
            self._load_mirrors()
        else:
            self._reattach_mirrors(game_hwnd, client)

    def _show_regions(self) -> None:
        """Refresh the region cards; before the profile is loaded, say what it waits for."""
        pending: str | None = None
        if self.profile.needs_load:
            if self.game.hwnd is None:
                pending = tr("This profile's mirrors appear once Tibia is running.")
            else:
                pending = tr("This profile's mirrors appear once Tibia is restored.")
        self.page.show_regions(self.mirrors, pending)

    def _show_connection(self) -> None:
        self.panel.set_connection(self.game.state())

    def _reattach_mirrors(self, game_hwnd: Hwnd, client: Rect) -> None:
        """Tibia was restarted: point the mirrors kept in memory at its new window."""
        failed = self.mirrors.attach(game_hwnd, client)
        self._show_regions()  # region sizes may follow a new client size
        if failed:
            self.page.set_status(
                tr_n(failed, "{n} mirror failed to reconnect", "{n} mirrors failed to reconnect"),
                "error",
            )
        self._apply_visibility()

    def _check_game(self) -> None:
        """Notice Tibia closing: detach the mirrors and wait for it to come back."""
        if not self.game.check_closed():
            return
        if self._selector is not None and self._selector.overlay.winfo_exists():
            self._selector.cancel()  # it was selecting from the closed window
        self.mirrors.detach()
        self._show_connection()
        self._show_regions()
        self._attach_poll()

    def _on_click(self, button: str, x: int, y: int, at: float) -> None:
        """A mouse button went down at (x, y): start the timers whose region it hit."""
        if self.game.hwnd is None or self.game.client is None:
            return
        if win32.toplevel_at(x, y) != self.game.hwnd:
            return  # another window at that spot got the click
        client_x, client_y = x - self.game.client.x, y - self.game.client.y
        for mirror in self.mirrors:
            if (
                mirror.timer.enabled
                and button_matches(mirror.timer, button)
                and mirror.rect.contains(client_x, client_y)
            ):
                self._start_timer(mirror, at)

    def _on_key(self, vk: int, modifiers: tuple[str, ...]) -> None:
        """A key went down: with Tibia in front, the hide-all key or the timers bound to it."""
        if self.game.hwnd is None or win32.foreground_window() != self.game.hwnd:
            return
        # A clash can still come in with a profile (imported, or set up before
        # the key was chosen): hiding wins, and the Timer dialog points it out.
        if combo_matches(self.settings.hide_all_combo, vk, modifiers):
            self._toggle_all_hidden()
            return
        now = time.monotonic()
        for mirror in self.mirrors:
            if mirror.timer.enabled and key_matches(mirror.timer, vk, modifiers):
                self._start_timer(mirror, now)

    # Each poll schedules its next run first, so an error in one run cannot stop it for good.
    def _timer_poll(self) -> None:
        self.root.after(TIMER_TICK_MS, self._timer_poll)
        now = time.monotonic()
        for mirror in self.mirrors:
            if mirror.tick_timer(now):
                sounds.play(mirror.timer.sound)

    def _visibility_poll(self) -> None:
        self.root.after(VISIBILITY_POLL_MS, self._visibility_poll)
        if self._instance.show_requested():
            win32.bring_to_front(self.panel_hwnd)
        self._check_game()
        self._check_character()
        self._track_client()
        self._apply_visibility()

    def _apply_visibility(self) -> None:
        fg = win32.foreground_window()
        if fg is not None:
            self._last_external = next_last_external(
                self._last_external,
                fg,
                win32.window_process_id(fg) == self._pid,
                win32.window_class(fg),
            )
        show = mirrors_should_show(
            self._last_external,
            self.game.hwnd,
            self.game.is_minimized(),
            self._selecting,
            self._all_hidden,
        )
        self.mirrors.set_visible(show)


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
