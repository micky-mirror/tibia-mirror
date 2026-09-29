"""When mirrors are shown (pure logic, unit-tested).

They show while Tibia is in front, or was the last window in front before one
of the app's own (panel, dialogs, mirrors) came up.
"""

from tibia_mirror.handles import Hwnd

# Shell windows that take the foreground for a moment while switching apps
# (taskbar, Alt+Tab). They don't count as where the user came from.
TRANSIENT_SHELL_CLASSES = frozenset(
    {
        "Shell_TrayWnd",
        "Shell_SecondaryTrayWnd",
        "MultitaskingViewFrame",
        "XamlExplorerHostIslandWindow",
        "TaskSwitcherWnd",
        "ForegroundStaging",
    }
)


def next_last_external(
    last_external: Hwnd | None,
    foreground: Hwnd | None,
    foreground_is_own: bool,
    foreground_class: str,
) -> Hwnd | None:
    """The most recent foreground window that is neither ours nor transient shell UI."""
    if foreground is None or foreground_is_own or foreground_class in TRANSIENT_SHELL_CLASSES:
        return last_external
    return foreground


def mirrors_should_show(
    last_external: Hwnd | None,
    game_hwnd: Hwnd | None,
    game_minimized: bool,
    selecting: bool,
    all_hidden: bool = False,
) -> bool:
    """Whether mirrors show: Tibia is (or was last) in front.

    Never while a region is being selected or after the hide-all key; mirrors
    hidden one by one are decided elsewhere.
    """
    if all_hidden or selecting or game_hwnd is None or game_minimized:
        return False
    return last_external == game_hwnd
