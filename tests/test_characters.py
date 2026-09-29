from tibia_mirror import characters
from tibia_mirror.characters import (
    character_in_title,
    characters_of,
    drop_profile,
    link,
    profile_for_new_character,
    profile_of,
    rename_profile,
    spelling,
    unlink,
)


def test_character_from_the_window_title():
    assert character_in_title("Tibia - Knight Name") == "Knight Name"
    assert character_in_title("Tibia") is None  # the login screen
    assert character_in_title("Tibia - ") is None
    assert character_in_title("TibiaMirror - mirror.py") is None


def test_several_characters_share_a_profile():
    links = link(link((), "Knight One", "EK"), "Knight Two", "EK")
    assert characters_of(links, "EK") == ["Knight One", "Knight Two"]
    assert characters_of(links, "ek") == ["Knight One", "Knight Two"]  # as Windows file names


def test_names_match_ignoring_case():
    links = link((), "Knight Name", "EK")
    assert profile_of(links, "knight name") == "EK"
    assert profile_of(links, "Someone Else") is None


def test_linking_again_moves_a_character():
    links = link(link((), "Knight Name", "EK"), "KNIGHT NAME", "MS")
    assert links == (("KNIGHT NAME", "MS"),)


def test_unlink():
    links = link(link((), "A", "EK"), "B", "EK")
    assert unlink(links, "a") == (("B", "EK"),)


def test_renaming_or_deleting_a_profile_carries_its_links():
    links = link(link((), "A", "EK"), "B", "MS")
    assert rename_profile(links, "ek", "Knights") == (("A", "Knights"), ("B", "MS"))
    assert drop_profile(links, "EK") == (("B", "MS"),)


def test_new_character_gets_a_profile_named_after_it():
    assert profile_for_new_character("Knight Name", ["Default"], ()) == ("Knight Name", False)


def test_an_unused_profile_with_its_name_is_taken_as_it_is():
    assert profile_for_new_character("Knight Name", ["knight name"], ()) == ("knight name", True)


def test_a_profile_with_its_name_used_by_another_character_is_left_alone():
    links = link((), "Other", "Knight Name")
    name, exists = profile_for_new_character("Knight Name", ["Knight Name"], links)
    assert (name, exists) == ("Knight Name copy", False)


def test_links_from_json_keep_only_sensible_pairs():
    data = {"Knight Name": "EK", " Druid ": "MS", "": "X", "Empty": "", "Number": 3}
    assert characters.from_json(data) == (("Druid", "MS"), ("Knight Name", "EK"))
    assert characters.from_json(["not", "an", "object"]) == ()


def test_a_linked_name_keeps_its_spelling():
    links = link((), "Druid Guy", "MS")
    assert spelling(links, "druid guy") == "Druid Guy"
    assert spelling(links, "new one") == "new one"
