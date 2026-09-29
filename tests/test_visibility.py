from tibia_mirror.visibility import mirrors_should_show, next_last_external

GAME, BROWSER, PANEL = 100, 200, 300


def test_external_foreground_becomes_last_external():
    assert next_last_external(None, GAME, False, "Qt6103QWindowIcon") == GAME
    assert next_last_external(GAME, BROWSER, False, "MozillaWindowClass") == BROWSER


def test_own_windows_keep_the_previous_app():
    # Panel, name dialog, overlay and mirrors all belong to this process.
    assert next_last_external(GAME, PANEL, True, "TkTopLevel") == GAME
    assert next_last_external(BROWSER, PANEL, True, "TkTopLevel") == BROWSER


def test_transient_shell_windows_are_ignored():
    for cls in ("Shell_TrayWnd", "XamlExplorerHostIslandWindow", "MultitaskingViewFrame"):
        assert next_last_external(GAME, 999, False, cls) == GAME


def test_no_foreground_keeps_the_previous_app():
    assert next_last_external(GAME, None, False, "") == GAME


def test_shown_when_tibia_was_last_in_front():
    assert mirrors_should_show(GAME, GAME, game_minimized=False, selecting=False)


def test_hidden_when_another_app_was_last_in_front():
    assert not mirrors_should_show(BROWSER, GAME, game_minimized=False, selecting=False)


def test_hidden_before_any_app_was_seen():
    assert not mirrors_should_show(None, GAME, game_minimized=False, selecting=False)


def test_hidden_while_selecting_a_region():
    assert not mirrors_should_show(GAME, GAME, game_minimized=False, selecting=True)


def test_hidden_while_tibia_is_minimized():
    assert not mirrors_should_show(GAME, GAME, game_minimized=True, selecting=False)


def test_hidden_before_tibia_is_detected():
    assert not mirrors_should_show(None, None, game_minimized=False, selecting=False)


def test_hidden_while_all_mirrors_are_hidden_with_the_key():
    assert not mirrors_should_show(
        GAME, GAME, game_minimized=False, selecting=False, all_hidden=True
    )
