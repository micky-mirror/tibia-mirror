from tibia_mirror.core.keys import canonical_modifiers, combo_matches, combo_name, parse_key


def test_modifiers_are_known_unique_and_in_order():
    assert canonical_modifiers(["shift", "ctrl", "shift", "super"]) == ("ctrl", "shift")
    assert canonical_modifiers(None) == ()
    assert canonical_modifiers("shift") == ()  # a plain string is not a list of names


def test_combo_name():
    assert combo_name((), "F9") == "F9"
    assert combo_name(("shift", "ctrl"), "F9") == "Ctrl+Shift+F9"
    assert combo_name(("alt",), "Q") == "Alt+Q"


def test_combos_match_exactly_with_their_modifiers():
    ctrl_h = (72, ("ctrl",))
    assert combo_matches(ctrl_h, 72, ("ctrl",))
    assert not combo_matches(ctrl_h, 72, ())
    assert not combo_matches(ctrl_h, 72, ("ctrl", "shift"))
    assert not combo_matches(None, 72, ())


def test_parse_key_keeps_only_virtual_key_codes():
    assert parse_key(120) == 120
    for bad in (None, 0, 256, -1, True, 1.5, "120"):
        assert parse_key(bad) is None
