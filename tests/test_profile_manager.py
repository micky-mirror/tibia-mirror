"""The profile manager: which profiles exist and which one it opens at the start."""

import json
from dataclasses import replace

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


def make_watched_manager(folder, settings, changes):
    """A profile manager that adds each change it reports to `changes`."""
    return ProfileManager(
        folder, settings, lambda previous, current: changes.append((previous, current))
    )


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


# Hotkeys as the app keeps them: (key code, modifiers held with it).
F1 = (112, ())
CTRL_F1 = (112, ("ctrl",))
F2 = (113, ())


def make_mirror_json_with_hotkey(mirror_id, hotkey):
    """One mirror as a profile file holds it, with a timer that `hotkey` starts."""
    key_code, modifiers = hotkey
    timer_json = {"enabled": True, "alert": 90, "key": key_code, "modifiers": list(modifiers)}
    return {**MIRROR_JSON, "id": mirror_id, "timer": timer_json}


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


def test_a_duplicated_profile_has_the_same_mirrors_with_new_ids(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))
    manager.load()

    manager.duplicate("Elite Knight")
    manager.open("Elite Knight")
    manager.load()

    original = MirrorSettings.from_json(MIRROR_JSON)
    copy = manager.current.mirrors[0]
    assert copy.mirror_id != original.mirror_id
    assert replace(copy, mirror_id=original.mirror_id) == original


def test_a_duplicate_does_not_change_the_open_profile(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))
    manager.load()

    manager.duplicate("Elite Knight")

    assert manager.active_name == "Knight"
    assert manager.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON),)


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


def test_an_updated_mirror_is_kept_and_saved(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    settings = make_settings(tmp_path, "Knight")
    manager = make_manager(folder, settings)
    manager.load()
    changed = replace(MirrorSettings.from_json(MIRROR_JSON), zoom=2.0)

    manager.update_mirror(changed)
    manager.save()

    next_start = make_manager(folder, settings)
    next_start.load()
    assert manager.current.mirrors == (changed,)
    assert next_start.current.mirrors == (changed,)


def test_only_the_mirror_with_the_same_id_is_updated(tmp_path, folder):
    health_json = {**MIRROR_JSON, "id": "mirror-2", "name": "Health"}
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON, health_json]})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))
    manager.load()
    changed_health = replace(MirrorSettings.from_json(health_json), zoom=2.0)

    manager.update_mirror(changed_health)

    assert manager.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON), changed_health)


def test_a_change_is_reported_with_the_profile_before_and_after_it(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    changes = []
    manager = make_watched_manager(folder, make_settings(tmp_path, "Knight"), changes)
    manager.load()
    mirror = MirrorSettings.from_json(MIRROR_JSON)
    changed = replace(mirror, zoom=2.0)

    manager.update_mirror(changed)

    assert changes == [(Profile(mirrors=(mirror,)), Profile(mirrors=(changed,)))]


def test_the_same_mirror_settings_are_not_reported(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    changes = []
    manager = make_watched_manager(folder, make_settings(tmp_path, "Knight"), changes)
    manager.load()

    manager.update_mirror(MirrorSettings.from_json(MIRROR_JSON))

    assert changes == []


def test_an_unknown_mirror_changes_nothing(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    changes = []
    manager = make_watched_manager(folder, make_settings(tmp_path, "Knight"), changes)
    manager.load()
    unknown = replace(MirrorSettings.from_json(MIRROR_JSON), mirror_id="mirror-2", zoom=2.0)

    manager.update_mirror(unknown)

    assert manager.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON),)
    assert changes == []


def test_an_updated_mirror_is_not_written_before_save(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    settings = make_settings(tmp_path, "Knight")
    manager = make_manager(folder, settings)
    manager.load()

    manager.update_mirror(replace(MirrorSettings.from_json(MIRROR_JSON), zoom=2.0))

    next_start = make_manager(folder, settings)
    next_start.load()
    assert next_start.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON),)


def test_a_removed_mirror_is_gone_and_the_others_keep_their_order(tmp_path, folder):
    health_json = {**MIRROR_JSON, "id": "mirror-2", "name": "Health"}
    mana_json = {**MIRROR_JSON, "id": "mirror-3", "name": "Mana"}
    saved_mirrors = [MIRROR_JSON, health_json, mana_json]
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": saved_mirrors})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))
    manager.load()

    manager.remove_mirror("mirror-2")

    assert manager.current.mirrors == (
        MirrorSettings.from_json(MIRROR_JSON),
        MirrorSettings.from_json(mana_json),
    )


def test_a_removal_is_reported_with_the_profile_before_and_after_it(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    changes = []
    manager = make_watched_manager(folder, make_settings(tmp_path, "Knight"), changes)
    manager.load()
    mirror = MirrorSettings.from_json(MIRROR_JSON)

    manager.remove_mirror("mirror-1")

    assert changes == [(Profile(mirrors=(mirror,)), Profile())]


def test_removing_an_unknown_mirror_changes_nothing(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    changes = []
    manager = make_watched_manager(folder, make_settings(tmp_path, "Knight"), changes)
    manager.load()

    manager.remove_mirror("mirror-2")

    assert manager.current.mirrors == (MirrorSettings.from_json(MIRROR_JSON),)
    assert changes == []


def test_a_timer_hotkey_is_cleared_in_every_mirror_that_uses_it(tmp_path, folder):
    saved_mirrors = [
        make_mirror_json_with_hotkey("mirror-1", F1),
        make_mirror_json_with_hotkey("mirror-2", CTRL_F1),
        make_mirror_json_with_hotkey("mirror-3", F1),
    ]
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": saved_mirrors})
    manager = make_manager(folder, make_settings(tmp_path, "Knight"))
    manager.load()

    manager.clear_hotkey(F1)

    assert [mirror.timer.key for mirror in manager.current.mirrors] == [None, CTRL_F1, None]


def test_a_cleared_timer_hotkey_is_reported_and_only_the_key_changes(tmp_path, folder):
    saved_mirrors = [make_mirror_json_with_hotkey("mirror-1", F1)]
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": saved_mirrors})
    changes = []
    manager = make_watched_manager(folder, make_settings(tmp_path, "Knight"), changes)
    manager.load()
    mirror = manager.current.mirrors[0]

    manager.clear_hotkey(F1)

    cleared_mirror = replace(mirror, timer=replace(mirror.timer, key=None))
    assert changes == [(Profile(mirrors=(mirror,)), Profile(mirrors=(cleared_mirror,)))]


def test_the_hide_all_key_is_cleared_when_it_is_the_hotkey(tmp_path, folder):
    settings = make_settings(tmp_path, "Default")
    settings.update(hide_all_key=F1)
    manager = make_manager(folder, settings)

    manager.clear_hotkey(F1)

    assert settings.current.hide_all_key is None


def test_a_hotkey_that_nothing_uses_changes_nothing(tmp_path, folder):
    saved_mirrors = [make_mirror_json_with_hotkey("mirror-1", F1)]
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": saved_mirrors})
    settings = make_settings(tmp_path, "Knight")
    settings.update(hide_all_key=CTRL_F1)
    changes = []
    manager = make_watched_manager(folder, settings, changes)
    manager.load()
    profile_before, settings_before = manager.current, settings.current

    manager.clear_hotkey(F2)

    assert manager.current == profile_before
    assert settings.current == settings_before
    assert changes == []


def test_a_loaded_profile_is_not_reported_as_a_change(tmp_path, folder):
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": [MIRROR_JSON]})
    changes = []
    manager = make_watched_manager(folder, make_settings(tmp_path, "Knight"), changes)

    manager.load()

    assert changes == []


def test_a_loaded_profile_loses_the_hide_all_key_from_its_timers(tmp_path, folder):
    saved_mirrors = [
        make_mirror_json_with_hotkey("mirror-1", F1),
        make_mirror_json_with_hotkey("mirror-2", CTRL_F1),
    ]
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": saved_mirrors})
    settings = make_settings(tmp_path, "Knight")
    settings.update(hide_all_key=F1)
    manager = make_manager(folder, settings)

    manager.load()

    assert [mirror.timer.key for mirror in manager.current.mirrors] == [None, CTRL_F1]
    assert settings.current.hide_all_key == F1


def test_the_hide_all_key_cleared_on_load_is_reported(tmp_path, folder):
    saved_mirrors = [make_mirror_json_with_hotkey("mirror-1", F1)]
    write_profile_file(folder, "Knight", {"version": 2, "mirrors": saved_mirrors})
    settings = make_settings(tmp_path, "Knight")
    settings.update(hide_all_key=F1)
    changes = []
    manager = make_watched_manager(folder, settings, changes)

    manager.load()

    mirror = MirrorSettings.from_json(saved_mirrors[0])
    cleared_mirror = replace(mirror, timer=replace(mirror.timer, key=None))
    assert changes == [(Profile(mirrors=(mirror,)), Profile(mirrors=(cleared_mirror,)))]


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
