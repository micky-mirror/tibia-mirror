from tibia_mirror.core.tibia.characters import character_in_title


def test_character_from_the_window_title():
    assert character_in_title("Tibia - Knight Name") == "Knight Name"
    assert character_in_title("Tibia") is None  # the login screen
    assert character_in_title("Tibia - ") is None
    assert character_in_title("TibiaMirror - mirror.py") is None
