from tibia_mirror.core.profiles import copy_name, name_error


def test_name_error():
    assert name_error("Knight", ["Druid"]) is None
    assert name_error("", []) == "Enter a name"
    assert name_error("a/b", []) is not None
    assert name_error("tab\there", []) is not None
    assert name_error("dot.", []) is not None
    assert name_error("space ", []) is not None
    assert name_error("con", []) == "That name is reserved by Windows"
    assert name_error("LPT1.json", []) == "That name is reserved by Windows"
    assert name_error("Console", []) is None
    assert name_error("knight", ["Knight"]) == "A profile with this name already exists"


def test_copy_name_finds_a_free_one():
    assert copy_name("Knight", ["Knight"]) == "Knight copy"
    assert copy_name("Knight", ["Knight", "knight COPY"]) == "Knight copy 2"
