"""The Shortcuts page: keys that act on the mirrors while Tibia is active (SettingsGroup cards)."""

import tkinter as tk

from tibia_mirror.i18n import tr
from tibia_mirror.settings import Settings
from tibia_mirror.ui.settings_page import KeyRow, OnChange, build_groups_page


def build_shortcuts_page(
    parent: tk.Misc, settings: Settings, *, width: int, pad: int, on_change: OnChange
) -> tk.Frame:
    """The Shortcuts page; on_change(key, value) may refuse a key by returning why."""
    groups = (
        (
            tr("MIRRORS"),
            [
                KeyRow(
                    "hide_all",
                    tr("Hide all mirrors"),
                    settings.hide_all_combo,
                    tr("Press again to bring them back. Works while Tibia is active."),
                ),
            ],
        ),
    )
    return build_groups_page(parent, groups, width=width, pad=pad, on_change=on_change)
