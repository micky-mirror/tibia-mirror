"""The profile manager: which profiles exist and which one it opens at the start."""

import json

import pytest

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.core.mirror_settings import MirrorSettings
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
    manager = ProfileManager(folder, make_settings(tmp_path, "Default"))

    assert manager.get_names() == ["Default"]
    assert manager.active_name == "Default"


def test_the_profile_of_the_last_time_is_opened(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")

    manager = ProfileManager(folder, make_settings(tmp_path, "Sorcerer"))

    assert manager.active_name == "Sorcerer"


def test_the_profile_of_the_last_time_is_found_in_other_letter_case(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")

    manager = ProfileManager(folder, make_settings(tmp_path, "sorcerer"))

    assert manager.active_name == "Sorcerer"


def test_the_first_profile_is_opened_when_the_last_one_is_gone(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")

    manager = ProfileManager(folder, make_settings(tmp_path, "Druid"))

    assert manager.active_name == "Knight"


def test_an_opened_profile_is_the_one_whose_mirrors_are_read(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": []})
    write_profile_file(folder, "Sorcerer", {"version": 2, "mirrors": [MIRROR_JSON]})
    manager = ProfileManager(folder, make_settings(tmp_path, "Knight"))

    manager.open("Sorcerer")

    assert manager.active_name == "Sorcerer"
    assert manager.read_mirrors() == [MirrorSettings.from_json(MIRROR_JSON)]


def test_an_opened_profile_is_opened_again_at_the_next_start(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")
    settings = make_settings(tmp_path, "Knight")
    ProfileManager(folder, settings).open("Sorcerer")

    next_start = ProfileManager(folder, settings)

    assert next_start.active_name == "Sorcerer"


def test_a_renamed_profile_keeps_its_mirrors_under_the_new_name(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    manager = ProfileManager(folder, make_settings(tmp_path, "Knight"))

    manager.rename("Elite Knight")

    assert manager.get_names() == ["Elite Knight"]
    assert manager.active_name == "Elite Knight"
    assert manager.read_mirrors() == [MirrorSettings.from_json(MIRROR_JSON)]


def test_a_renamed_profile_is_opened_again_at_the_next_start(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")
    settings = make_settings(tmp_path, "Knight")
    ProfileManager(folder, settings).rename("Team hunt")

    next_start = ProfileManager(folder, settings)

    assert next_start.active_name == "Team hunt"


def test_characters_linked_to_a_renamed_profile_stay_linked(tmp_path, folder):
    add_profile(folder, "Knight")
    settings = make_settings(tmp_path, "Knight")
    settings.update(character_links=(("Bubble", "Knight"),))
    manager = ProfileManager(folder, settings)

    manager.rename("Team hunt")

    assert settings.current.character_links == (("Bubble", "Team hunt"),)


def test_a_deleted_profile_is_gone_and_the_first_profile_left_is_opened(tmp_path, folder):
    add_profile(folder, "Druid")
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")
    settings = make_settings(tmp_path, "Druid")
    manager = ProfileManager(folder, settings)

    manager.delete()

    assert manager.get_names() == ["Knight", "Sorcerer"]
    assert manager.active_name == "Knight"
    assert settings.current.last_profile == "Knight"


def test_characters_linked_to_a_deleted_profile_lose_their_link(tmp_path, folder):
    add_profile(folder, "Knight")
    add_profile(folder, "Sorcerer")
    settings = make_settings(tmp_path, "Knight")
    settings.update(character_links=(("Bubble", "Knight"), ("Cachero", "Sorcerer")))
    manager = ProfileManager(folder, settings)

    manager.delete()

    assert settings.current.character_links == (("Cachero", "Sorcerer"),)


def test_the_mirrors_of_the_open_profile_are_read(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    write_profile_file(folder, "Sorcerer", {"version": 2, "mirrors": []})
    manager = ProfileManager(folder, make_settings(tmp_path, "Knight"))

    mirrors = manager.read_mirrors()

    assert mirrors == [MirrorSettings.from_json(MIRROR_JSON)]


def test_written_mirrors_are_read_back(tmp_path, folder):
    manager = ProfileManager(folder, make_settings(tmp_path, "Default"))
    mirrors = [MirrorSettings.from_json(MIRROR_JSON)]

    manager.write_mirrors(manager.active_name, mirrors)

    assert manager.read_mirrors() == mirrors


def test_the_first_default_profile_has_no_mirrors(tmp_path, folder):
    manager = ProfileManager(folder, make_settings(tmp_path, "Default"))

    assert manager.read_mirrors() == []


def test_a_file_that_is_only_a_list_of_mirrors_is_read(tmp_path, folder):
    write_profile_file(folder, "Knight", [MIRROR_JSON])
    manager = ProfileManager(folder, make_settings(tmp_path, "Knight"))

    mirrors = manager.read_mirrors()

    assert mirrors == [MirrorSettings.from_json(MIRROR_JSON)]


def test_broken_json_raises_value_error(tmp_path, folder):
    folder.mkdir()
    (folder / "Knight.json").write_text("{ this is not JSON", encoding="utf-8")
    manager = ProfileManager(folder, make_settings(tmp_path, "Knight"))

    with pytest.raises(ValueError):
        manager.read_mirrors()


def test_a_file_without_mirrors_raises_value_error(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2})
    manager = ProfileManager(folder, make_settings(tmp_path, "Knight"))

    with pytest.raises(ValueError, match="the profile file is invalid"):
        manager.read_mirrors()


def test_a_layout_without_region_raises_value_error(tmp_path, folder):
    broken_mirror = {**MIRROR_JSON, "layouts": {"1920x1080": {"offset": [5, 6]}}}
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [broken_mirror]})
    manager = ProfileManager(folder, make_settings(tmp_path, "Knight"))

    with pytest.raises(ValueError, match="the profile file is invalid"):
        manager.read_mirrors()


def test_a_deleted_file_raises_os_error(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": []})
    manager = ProfileManager(folder, make_settings(tmp_path, "Knight"))
    (folder / "Knight.json").unlink()

    with pytest.raises(OSError):
        manager.read_mirrors()
