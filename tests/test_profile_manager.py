"""The profile manager: which profiles exist and which one it opens at the start."""

import json

import pytest

from tibia_mirror.app_parts.profile_manager import ProfileManager
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
