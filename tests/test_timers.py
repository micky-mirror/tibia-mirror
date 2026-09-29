from tibia_mirror.timers import (
    TimerSettings,
    badge_text,
    button_matches,
    canonical_modifiers,
    clock,
    combo_matches,
    combo_name,
    is_done,
    key_clashes,
    key_matches,
    parse_alert,
    parse_key,
    pauses_from_json,
    pauses_of,
    pauses_to_json,
    with_pauses,
    without_mirrors,
)

DOWN = TimerSettings(enabled=True, alert=60, direction="down")
UP = TimerSettings(enabled=True, alert=60, direction="up")


def test_clock():
    assert clock(0) == "00:00"
    assert clock(75) == "01:15"
    assert clock(3599) == "59:59"
    assert clock(99999) == "59:59"


def test_before_the_first_start_it_shows_where_it_begins():
    assert badge_text(DOWN, None) == "01:00"
    assert badge_text(UP, None) == "00:00"


def test_counting_down_rounds_up_so_it_ends_on_zero():
    assert badge_text(DOWN, 0) == "01:00"
    assert badge_text(DOWN, 0.2) == "01:00"
    assert badge_text(DOWN, 59.5) == "00:01"
    assert badge_text(DOWN, 60) == "00:00"
    assert badge_text(DOWN, 500) == "00:00"  # stays on its final value


def test_counting_up_shows_whole_seconds_and_stops_at_the_alert():
    assert badge_text(UP, 0.9) == "00:00"
    assert badge_text(UP, 42.3) == "00:42"
    assert badge_text(UP, 500) == "01:00"


def test_done():
    assert not is_done(DOWN, None)
    assert not is_done(DOWN, 59.9)
    assert is_done(DOWN, 60)


def test_buttons():
    assert button_matches(TimerSettings(button="both"), "left")
    assert button_matches(TimerSettings(button="both"), "right")
    assert button_matches(TimerSettings(button="left"), "left")
    assert not button_matches(TimerSettings(button="left"), "right")


def test_parse_alert():
    assert parse_alert("1", "00") == 60
    assert parse_alert("0", "1") == 1
    assert parse_alert("59", "59") == 3599
    assert parse_alert("0", "0") is None
    assert parse_alert("60", "0") is None
    assert parse_alert("1", "60") is None
    assert parse_alert("", "5") is None


def test_settings_round_trip_and_bad_values_fall_back():
    settings = TimerSettings(True, 90, "up", "right", 116, "beep", ("ctrl", "shift"))
    assert TimerSettings.from_json(settings.to_json()) == settings
    bad = {
        "enabled": 1,
        "alert": 99999,
        "direction": "sideways",
        "button": "middle",
        "key": 999,
        "sound": "gong",
        "modifiers": ["hyper"],
    }
    assert TimerSettings.from_json(bad) == TimerSettings()
    assert TimerSettings.from_json(None) == TimerSettings()


def test_modifiers_are_known_unique_and_in_order():
    assert canonical_modifiers(["shift", "ctrl", "shift", "super"]) == ("ctrl", "shift")
    assert canonical_modifiers(None) == ()
    assert canonical_modifiers("shift") == ()  # a plain string is not a list of names


def test_combo_name():
    assert combo_name((), "F9") == "F9"
    assert combo_name(("shift", "ctrl"), "F9") == "Ctrl+Shift+F9"
    assert combo_name(("alt",), "Q") == "Alt+Q"


def test_keys_match_exactly_with_their_modifiers():
    shift_f9 = TimerSettings(enabled=True, key=120, modifiers=("shift",))
    assert key_matches(shift_f9, 120, ("shift",))
    assert not key_matches(shift_f9, 120, ())
    assert not key_matches(shift_f9, 120, ("ctrl", "shift"))
    plain_f9 = TimerSettings(enabled=True, key=120)
    assert key_matches(plain_f9, 120, ())
    assert not key_matches(plain_f9, 120, ("shift",))


def test_a_timer_without_a_key_matches_no_key():
    assert not key_matches(TimerSettings(enabled=True), 120, ())


def test_combos_match_exactly_with_their_modifiers():
    ctrl_h = (72, ("ctrl",))
    assert combo_matches(ctrl_h, 72, ("ctrl",))
    assert not combo_matches(ctrl_h, 72, ())
    assert not combo_matches(ctrl_h, 72, ("ctrl", "shift"))
    assert not combo_matches(None, 72, ())


def test_only_a_timer_that_is_on_clashes_with_a_key():
    shift_f9 = (120, ("shift",))
    on = TimerSettings(enabled=True, key=120, modifiers=("shift",))
    assert key_clashes(on, shift_f9)
    assert not key_clashes(on, (120, ()))
    assert not key_clashes(on, None)
    assert not key_clashes(TimerSettings(enabled=False, key=120, modifiers=("shift",)), shift_f9)
    assert not key_clashes(TimerSettings(enabled=True), shift_f9)


def test_parse_key_keeps_only_virtual_key_codes():
    assert parse_key(120) == 120
    for bad in (None, 0, 256, -1, True, 1.5, "120"):
        assert parse_key(bad) is None


def test_offline_pause_is_saved_and_only_counts_for_a_timer_that_is_on():
    settings = TimerSettings(enabled=True, offline_pause=True)
    assert TimerSettings.from_json(settings.to_json()) == settings
    assert settings.pauses_offline
    assert not TimerSettings(enabled=False, offline_pause=True).pauses_offline


def test_offline_pause_is_on_unless_saved_off():
    assert TimerSettings().offline_pause is True
    assert TimerSettings.from_json({}).offline_pause is True
    assert TimerSettings.from_json({"offline_pause": "yes"}).offline_pause is True
    assert TimerSettings.from_json({"offline_pause": False}).offline_pause is False


def test_each_character_keeps_its_own_pauses():
    pauses = with_pauses((), "Knight One", {"m1": 200.0})
    pauses = with_pauses(pauses, "Knight Two", {"m1": 15.0, "m2": 3.0})
    assert pauses_of(pauses, "Knight One") == {"m1": 200.0}
    assert pauses_of(pauses, "Knight Two") == {"m1": 15.0, "m2": 3.0}
    assert pauses_of(pauses, "Nobody") == {}


def test_a_login_takes_the_characters_pauses_and_a_logout_replaces_them():
    pauses = with_pauses((), "Knight One", {"m1": 200.0})
    pauses = with_pauses(pauses, "Knight One", {})  # logged in: now running
    assert pauses == ()
    pauses = with_pauses(pauses, "Knight One", {"m2": 12.34})
    assert pauses == (("Knight One", "m2", 12.3),)


def test_forgotten_mirrors_leave_no_pauses():
    pauses = with_pauses(with_pauses((), "A", {"m1": 1.0, "m2": 2.0}), "B", {"m1": 3.0})
    assert without_mirrors(pauses, {"m1"}) == (("A", "m2", 2.0),)


def test_pauses_json_round_trip_drops_nonsense():
    pauses = with_pauses(with_pauses((), "A", {"m1": 1.5}), "B", {"m2": 30.0})
    assert pauses_from_json(pauses_to_json(pauses)) == pauses
    messy = {"A": {"m1": 1, "m2": True, "m3": -4, "m4": "x"}, "B": [1], "C": {}}
    assert pauses_from_json(messy) == (("A", "m1", 1.0),)
    assert pauses_from_json("nope") == ()
