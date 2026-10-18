"""The profile manager: which profiles exist and which one it opens at the start."""

import json

import pytest

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.profile import Profile
from tibia_mirror.core.profiles import ProfileStore
from tibia_mirror.settings.app_settings_store import AppSettingsStore


@pytest.fixture
def folder(tmp_path):
    """The folder of the profile files. It does not exist until a profile is saved."""
    return tmp_path / "profiles"


def add_profile(folder, name):
    ProfileStore(folder).save(name, [])


def make_settings(tmp_path, last_profile):
    """Settings that remember `last_profile` as the profile that was open the last time."""
    file = tmp_path / "settings.json"
    file.write_text(json.dumps({"profile": last_profile}), encoding="utf-8")
    return AppSettingsStore(file, lambda previous, current: None)


def make_manager(folder, settings):
    """A profile manager that tells nobody about its changes."""
    return ProfileManager(folder, settings, lambda previous, current: None)


# One mirror as a profile file holds it.
MIRROR_JSON = {
    "id": "mirror-1",
    "name": "Minimap",
    "layouts": {"1920x1080": {"region": [10, 20, 300, 40], "offset": [5, 6]}},
}


def write_profile_file(folder, name, data):
    """Write `data` as the file of the profile `name`."""
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / f"{name}.json"
    file.write_text(json.dumps(data), encoding="utf-8")


def test_the_first_start_creates_the_default_profile(tmp_path, folder):
    manager = make_manager(folder, make_settings(tmp_path, "Default"))

    assert manager.get_names() == ["Default"]
    assert manager.active_name == "Default"


def test_the_profile_of_the_last_time_is_opened(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")

    manager = make_manager(folder, make_settings(tmp_path, "Sorcerer"))

    assert manager.active_name == "Sorcerer"


def test_the_profile_of_the_last_time_is_found_in_other_letter_case(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")

    manager = make_manager(folder, make_settings(tmp_path, "sorcerer"))

    assert manager.active_name == "Sorcerer"


def test_the_first_profile_is_opened_when_the_last_one_is_gone(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")

    manager = make_manager(folder, make_settings(tmp_path, "Druid"))

    assert manager.active_name == "Knight"


def test_a_profile_name_is_found_in_other_letter_case(tmp_path, folder):
    add_profile(folder, "Knight")
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    assert manager.find_name("KNIGHT") == "Knight"


def test_a_missing_profile_name_is_not_found(tmp_path, folder):
    add_profile(folder, "Knight")
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    assert manager.find_name("Sorcerer") is None


def test_an_opened_profile_is_the_one_whose_mirrors_are_read(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": []})
    write_profile_file(folder, "Sorcerer", {"version": 2, "mirrors": [MIRROR_JSON]})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    manager.open("Sorcerer")
    manager.load()

    assert manager.active_name == "Sorcerer"
    assert manager.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON),)


def test_an_opened_profile_is_opened_again_at_the_next_start(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")
    settings = make_settings(tmp_path, "Knight")
    make_manager(folder, settings).open("Sorcerer")

    next_start = make_manager(folder, settings)

    assert next_start.active_name == "Sorcerer"


def test_a_renamed_profile_keeps_its_mirrors_under_the_new_name(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    manager.rename("Elite Knight")
    manager.load()

    assert manager.get_names() == ["Elite Knight"]
    assert manager.active_name == "Elite Knight"
    assert manager.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON),)


def test_a_renamed_profile_is_opened_again_at_the_next_start(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")
    settings = make_settings(tmp_path, "Knight")
    make_manager(folder, settings).rename("Team hunt")

    next_start = make_manager(folder, settings)

    assert next_start.active_name == "Team hunt"


def test_a_deleted_profile_is_gone_and_the_first_profile_left_is_opened(tmp_path, folder):
    add_profile(folder, "Druid")
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")
    settings = make_settings(tmp_path, "Druid")
    manager = make_manager(folder, settings)

    manager.delete()

    assert manager.get_names() == ["Knight", "Sorcerer"]
    assert manager.active_name == "Knight"
    assert settings.current.last_profile == "Knight"


def test_the_mirrors_of_the_open_profile_are_read(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    write_profile_file(folder, "Sorcerer", {"version": 2, "mirrors": []})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    manager.load()

    assert manager.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON),)


def test_written_mirrors_are_read_back(tmp_path, folder):
    manager = make_manager(folder, make_settings(tmp_path, "Default"))
    mirrors = [MirrorSettings.from_json(MIRROR_JSON)]

    manager.write_mirrors(manager.active_name, mirrors)
    manager.load()

    assert manager.current.mirrors == tuple(mirrors)


def test_set_mirrors_are_kept_and_saved(tmp_path, folder):
    settings = make_settings(tmp_path, "Default")
    manager = make_manager(folder, settings)
    mirror = MirrorSettings.from_json(MIRROR_JSON)

    manager.set_mirrors([mirror])
    manager.save()

    next_start = make_manager(folder, settings)
    next_start.load()
    assert manager.current.mirrors == (mirror,)
    assert next_start.current.mirrors == (mirror,)


def test_the_first_default_profile_has_no_mirrors(tmp_path, folder):
    manager = make_manager(folder, make_settings(tmp_path, "Default"))
    manager.load()

    assert manager.current.mirrors == ()


def test_a_file_that_is_only_a_list_of_mirrors_is_read(tmp_path, folder):
    write_profile_file(folder, "Knight", [MIRROR_JSON])
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    manager.load()

    assert manager.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON),)


def test_broken_json_raises_value_error(tmp_path, folder):
    folder.mkdir()
    (folder / "Knight.json").write_text("{ this is not JSON", encoding="utf-8")
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    with pytest.raises(ValueError):
        manager.load()


def test_a_file_without_mirrors_raises_value_error(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    with pytest.raises(ValueError, match="the profile file is invalid"):
        manager.load()


def test_a_layout_without_region_raises_value_error(tmp_path, folder):
    broken_mirror = {**MIRROR_JSON, "layouts": {"1920x1080": {"offset": [5, 6]}}}
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [broken_mirror]})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))

    with pytest.raises(ValueError, match="the profile file is invalid"):
        manager.load()


def test_a_deleted_file_raises_os_error(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": []})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))
    (folder / "Knight.json").unlink()

    with pytest.raises(OSError):
        manager.load()


def test_a_profile_that_fails_to_load_is_kept_empty(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    write_profile_file(folder, "Sorcerer", {"version": 2})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))
    manager.load()

    manager.open("Sorcerer")
    with pytest.raises(ValueError):
        manager.load()

    assert manager.current == Profile()
