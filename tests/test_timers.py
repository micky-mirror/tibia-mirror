from tibia_mirror.core.timers import (
    clock,
    parse_alert,
    pauses_from_json,
    pauses_of,
    pauses_to_json,
    with_pauses,
    without_mirrors,
)


def test_clock():
    assert clock(0) == "00:00"
    assert clock(75) == "01:15"
    assert clock(3599) == "59:59"
    assert clock(99999) == "59:59"


def test_parse_alert():
    assert parse_alert("1", "00") == 60
    assert parse_alert("0", "1") == 1
    assert parse_alert("59", "59") == 3599
    assert parse_alert("0", "0") is None
    assert parse_alert("60", "0") is None
    assert parse_alert("1", "60") is None
    assert parse_alert("", "5") is None


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
