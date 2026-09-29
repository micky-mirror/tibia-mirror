from tibia_mirror.config import DEFAULT_PROFILE
from tibia_mirror.geometry import Rect
from tibia_mirror.profiles import ProfileStore, copy_name, name_error
from tibia_mirror.regions import Layout, SavedRegion

CD = SavedRegion("Cooldowns", {"1600x900": Layout(Rect(1, 2, 3, 4), (5, 6))})


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


def test_store_round_trip_and_sorting(tmp_path):
    store = ProfileStore(tmp_path / "profiles")
    assert store.names() == []
    store.save("knight", [CD])
    store.save("Druid", [])
    assert store.names() == ["Druid", "knight"]
    assert store.load("knight") == [CD]
    assert store.load("Gone") == []


def test_rename_and_delete(tmp_path):
    store = ProfileStore(tmp_path)
    store.save("knight", [CD])
    store.rename("knight", "Knight")  # case-only rename
    assert store.names() == ["Knight"]
    assert store.load("Knight") == [CD]
    store.delete("Knight")
    assert store.names() == []


def test_copy_duplicates_the_file_verbatim(tmp_path):
    store = ProfileStore(tmp_path)
    store.save("Knight", [CD])
    store.copy("Knight", "Knight copy")
    assert (tmp_path / "Knight copy.json").read_bytes() == (tmp_path / "Knight.json").read_bytes()


def test_ensure_one_creates_an_empty_default_the_first_time(tmp_path):
    store = ProfileStore(tmp_path / "profiles")
    store.ensure_one()
    assert store.names() == [DEFAULT_PROFILE]
    assert store.load(DEFAULT_PROFILE) == []


def test_ensure_one_leaves_existing_profiles_alone(tmp_path):
    store = ProfileStore(tmp_path / "profiles")
    store.save("Knight", [CD])
    store.ensure_one()
    assert store.names() == ["Knight"]


def test_export_copies_the_saved_file_anywhere(tmp_path):
    store = ProfileStore(tmp_path / "profiles")
    store.save("Knight", [CD])
    target = tmp_path / "elsewhere" / "knight.json"
    target.parent.mkdir()
    store.export("Knight", target)
    assert target.read_bytes() == (tmp_path / "profiles" / "Knight.json").read_bytes()
