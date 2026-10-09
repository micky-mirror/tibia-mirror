"""The Mirrors page: profile picker, Add region, the region list, Save/Revert."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from tibia_mirror.core.geometry import Box, Point
from tibia_mirror.i18n import tr, tr_n
from tibia_mirror.ui import theme
from tibia_mirror.ui.menu import SEPARATOR, MenuItem, PopupMenu, ProfilePicker
from tibia_mirror.ui.render import margins
from tibia_mirror.ui.scale import px
from tibia_mirror.ui.text import elide
from tibia_mirror.ui.widgets import RaisedButton, RegionCard, ScrollList

if TYPE_CHECKING:
    # Only named in annotations: the page never imports the mirror window itself.
    from tibia_mirror.ui.mirror import MirrorWindow

TONES = {"muted": "SUBTEXT", "ok": "GREEN", "error": "RED"}  # theme colour names
# Sizes at 100% display scaling, scaled with px() where used.
BUTTON_GAP = 12
STATUS_GAP = 12  # at least this much between the REGIONS heading and the status


def region_count(count: int) -> str:
    return tr_n(count, "{n} region", "{n} regions")


@dataclass(frozen=True)
class RegionActions:
    """What a region card asks the App to do with its mirror (each gets the mirror first)."""

    remove: Callable[[MirrorWindow], None]
    hover: Callable[[MirrorWindow, bool], None]
    set_opacity: Callable[[MirrorWindow, float], None]
    adjust: Callable[[MirrorWindow, bool], None]
    rename: Callable[[MirrorWindow, Point], None]  # Point: its card's centre on screen
    resize: Callable[[MirrorWindow, Point], None]
    set_hidden: Callable[[MirrorWindow, bool], None]
    set_locked: Callable[[MirrorWindow, bool], None]
    set_color: Callable[[MirrorWindow, str], None]  # a frame colour name
    timer: Callable[[MirrorWindow, Point], None]  # open its Timer dialog


@dataclass(frozen=True)
class ProfileActions:
    select: Callable[[str], None]  # a profile name
    new: Callable[[], None]
    duplicate: Callable[[], None]
    rename: Callable[[], None]
    characters: Callable[[], None]
    copy_from: Callable[[], None]
    delete: Callable[[], None]
    import_file: Callable[[], None]
    export_file: Callable[[], None]


@dataclass(frozen=True)
class MirrorsActions:
    add: Callable[[], None]
    save: Callable[[], object]  # returns whether it worked, which the page ignores
    revert: Callable[[], None]
    region: RegionActions
    profile: ProfileActions


class MirrorsPage(tk.Frame):
    """Pure view: every button forwards to a callback supplied by the App."""

    def __init__(self, parent: tk.Misc, actions: MirrorsActions, *, width: int, pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._actions = actions
        self._width = width
        self._profiles: list[str] = []
        self._active = ""

        self._picker = ProfilePicker(self, width=width, on_open=self._open_profile_menu)
        self._picker.pack(anchor="w", padx=pad, pady=(px(18), 0))

        add = RaisedButton(
            self,
            "+  " + tr("Add region"),
            actions.add,
            width=width,
            height=px(42),
            style=theme.PRIMARY_BUTTON,
            hover_fill=theme.ACCENT_HI,
            font=theme.FONT_BUTTON,
            fg=theme.ON_ACCENT,
            background=theme.BG,
        )
        header = tk.Frame(self, bg=theme.BG, width=width, height=px(20))
        header.pack_propagate(False)
        header.pack(anchor="w", padx=pad, pady=(px(20), max(0, px(8) - add.margins.top)))
        heading = tk.Label(
            header, text=tr("REGIONS"), bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT_CAPTION
        )
        heading.place(x=0, rely=0.5, anchor="w")
        # The status shares the heading's row, so a long one is cut short to fit beside it.
        self._status_width = width - heading.winfo_reqwidth() - px(STATUS_GAP)
        self._status_font = tkfont.Font(font=theme.FONT)
        self._status = tk.Label(header, bg=theme.BG, font=theme.FONT)
        self._status.place(relx=1.0, rely=0.5, anchor="e")
        add.pack(anchor="w", padx=(pad - add.margins.left, 0))

        # Packed before the list so they keep their space at the bottom.
        self._save_state = tk.Label(self, bg=theme.BG, font=theme.FONT)
        self._save_state.pack(side="bottom", anchor="w", padx=pad, pady=(0, px(14)))
        self._save_row = tk.Frame(self, bg=theme.BG)
        # Tk can't overlap the two canvases, so the gap holds both shadow margins at least.
        shadow = margins(theme.SAVE_BUTTON)
        gap = max(px(BUTTON_GAP), shadow.left + shadow.right)
        self._save, self._revert = (
            RaisedButton(
                self._save_row,
                label,
                command,
                width=(width - gap) // 2,
                height=px(34),
                style=style,
                hover_fill=hover,
                font=theme.FONT_BOLD,
                fg=fg,
                background=theme.BG,
            )
            # Save is the main action; Revert, which drops the changes, is a plain one
            # like a dialog's Cancel, so it isn't hit by mistake.
            for label, command, style, hover, fg in (
                (tr("Save"), actions.save, theme.SAVE_BUTTON, theme.GREEN_HI, theme.ON_ACCENT),
                (
                    tr("Revert"),
                    actions.revert,
                    theme.SECONDARY_BUTTON,
                    theme.SURFACE_HI,
                    theme.TEXT,
                ),
            )
        )
        self._save_row_padx = pad - shadow.left
        # The buttons' shadow margin below is the gap to the save state line.
        self._pack_save_row()
        self._save.pack(side="left")
        self._revert.pack(side="left", padx=(gap - shadow.right - shadow.left, 0))

        self.region_list = ScrollList(self, width=width)
        self.region_list.pack(anchor="w", fill="y", expand=True, padx=(pad, 0), pady=(px(2), px(8)))
        self._autosave = False
        self.set_unsaved(False)

    def _pack_save_row(self, after: tk.Misc | None = None) -> None:
        padx = (self._save_row_padx, 0)
        if after is None:
            self._save_row.pack(side="bottom", anchor="w", padx=padx)
        else:
            self._save_row.pack(side="bottom", anchor="w", padx=padx, after=after)

    # ---- state from the App -------------------------------------------------
    def set_profiles(self, names: Iterable[str], active: str) -> None:
        self._profiles, self._active = list(names), active
        self._picker.set_name(active)

    def set_autosave(self, autosave: bool) -> None:
        """With auto-save on, Save/Revert are gone and the line under them says so."""
        self._autosave = autosave
        if autosave:
            self._save_row.pack_forget()
            self._save_state.config(text=tr("Changes are saved automatically"), fg=theme.SUBTEXT)
        else:
            # Bottom-side packing stacks upwards: packing after the line puts the row above it.
            self._pack_save_row(after=self._save_state)
            self.set_unsaved(self._unsaved)

    def set_unsaved(self, unsaved: bool) -> None:
        self._unsaved = unsaved
        if self._autosave:
            return
        self._save.set_enabled(unsaved)
        self._revert.set_enabled(unsaved)
        if unsaved:
            self._save_state.config(text=tr("Unsaved changes - press Save"), fg=theme.YELLOW)
        else:
            self._save_state.config(text=tr("All changes saved"), fg=theme.SUBTEXT)

    def set_status(self, text: str, tone: str = "muted") -> None:
        text = elide(text, self._status_font, self._status_width)
        self._status.config(text=text, fg=getattr(theme, TONES[tone]))

    def show_regions(self, mirrors: Sequence[MirrorWindow], pending: str | None = None) -> None:
        """Cards for `mirrors`; with none, `pending` (why they are not loaded yet) or a hint."""
        for child in self.region_list.inner.winfo_children():
            if isinstance(child, RegionCard):
                child.release_hover()
            child.destroy()
        self.set_status("" if pending else region_count(len(mirrors)))
        if not mirrors:
            hint = tr("Click Add region, then drag a box over the part of the game to mirror.")
            tk.Label(
                self.region_list.inner,
                text=pending or hint,
                bg=theme.BG,
                fg=theme.SUBTEXT,
                font=theme.FONT,
                justify="left",
                wraplength=self._width,
            ).pack(anchor="w", pady=(px(10), 0))
            return
        actions = self._actions.region
        for mirror in mirrors:
            RegionCard(
                self.region_list.inner,
                mirror.name,
                f"{mirror.rect.w}×{mirror.rect.h}",
                mirror.opacity,
                hidden=mirror.hidden,
                locked=mirror.locked,
                color=mirror.color,
                width=self._width,
                on_remove=partial(actions.remove, mirror),
                on_hover=partial(actions.hover, mirror),
                on_opacity=partial(actions.set_opacity, mirror),
                on_adjust=partial(actions.adjust, mirror),
                on_rename=partial(actions.rename, mirror),
                on_resize=partial(actions.resize, mirror),
                on_color=partial(actions.set_color, mirror),
                on_timer=partial(actions.timer, mirror),
                timer_on=mirror.timer.enabled,
                timer_alert=mirror.timer.alert,
                on_hidden=partial(actions.set_hidden, mirror),
                on_locked=partial(actions.set_locked, mirror),
            ).pack(anchor="w", pady=(0, px(6)))

    # ---- profile menu -------------------------------------------------------
    def _open_profile_menu(self, box: Box) -> None:
        actions = self._actions.profile
        items: list[MenuItem | None] = [
            MenuItem(name, partial(actions.select, name), checked=name == self._active)
            for name in self._profiles
        ]
        items += [
            SEPARATOR,
            MenuItem(tr("New profile…"), actions.new),
            MenuItem(tr("Duplicate…"), actions.duplicate),
            MenuItem(tr("Rename…"), actions.rename),
            SEPARATOR,
            MenuItem(tr("Characters…"), actions.characters),
            MenuItem(tr("Copy from…"), actions.copy_from, enabled=len(self._profiles) > 1),
            SEPARATOR,
            MenuItem(tr("Import…"), actions.import_file),
            MenuItem(tr("Export…"), actions.export_file),
            SEPARATOR,
            MenuItem(
                tr("Delete profile"), actions.delete, enabled=len(self._profiles) > 1, danger=True
            ),
        ]
        PopupMenu(self.winfo_toplevel(), box, items, on_close=lambda: self._picker.set_open(False))
