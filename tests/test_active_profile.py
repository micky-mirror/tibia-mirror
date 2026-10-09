from dataclasses import replace

import pytest

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.profiles import ProfileStore
from tibia_mirror.core.regions import Layout, SavedRegion
from tibia_mirror.services.active_profile import LOAD_ERRORS, ActiveProfile

CD = SavedRegion("Cooldowns", {"1600x900": Layout(Rect(1, 2, 3, 4), (5, 6))})


class BrokenStore(ProfileStore):
    """A store that cannot write, like a full disk."""

    def save(self, name, saved):
        raise OSError("disk full")

    def rename(self, old, new):
        raise OSError("disk full")


@pytest.fixture
def store(tmp_path):
    return ProfileStore(tmp_path)


@pytest.fixture
def profile(store):
    return ActiveProfile(store, "Knight")


def test_a_new_profile_without_mirrors_has_nothing_unsaved(profile):
    assert not profile.has_unsaved([])


def test_a_mirror_that_was_never_saved_is_unsaved(profile):
    assert profile.has_unsaved([CD])


def test_nothing_is_unsaved_right_after_mark_saved(profile):
    profile.mark_saved([CD])
    assert not profile.has_unsaved([CD])


def test_a_changed_mirror_is_unsaved(profile):
    profile.mark_saved([CD])
    assert profile.has_unsaved([replace(CD, hidden=True)])


def test_a_removed_mirror_is_unsaved(profile):
    profile.mark_saved([CD])
    assert profile.has_unsaved([])


def test_save_writes_the_file_and_leaves_nothing_unsaved(profile, store):
    profile.save([CD])
    assert store.load("Knight") == [CD]
    assert not profile.has_unsaved([CD])


def test_a_failed_save_keeps_the_changes_unsaved(tmp_path):
    profile = ActiveProfile(BrokenStore(tmp_path), "Knight")
    with pytest.raises(OSError, match="disk full"):
        profile.save([CD])
    assert profile.has_unsaved([CD])


def test_load_reads_the_file_and_leaves_nothing_unsaved(profile, store):
    store.save("Knight", [replace(CD, id="abc")])
    mirrors = profile.load(None)
    assert mirrors == [replace(CD, id="abc")]
    assert not profile.has_unsaved(mirrors)
    assert not profile.needs_load


def test_load_gives_no_mirrors_when_the_file_is_missing(profile):
    assert profile.load(None) == []
    assert not profile.has_unsaved([])


def test_load_of_a_broken_file_raises_and_remembers_an_empty_profile(profile, tmp_path):
    (tmp_path / "Knight.json").write_text("this is not a profile", encoding="utf-8")
    with pytest.raises(LOAD_ERRORS):
        profile.load(None)
    assert not profile.needs_load
    assert not profile.has_unsaved([])


def test_load_gives_ids_to_old_mirrors_and_writes_them_to_the_file(profile, store):
    store.save("Knight", [CD])  # CD has no id, like a mirror from an old file
    mirrors = profile.load(None)
    assert mirrors[0].id
    assert store.load("Knight") == mirrors
    assert not profile.has_unsaved(mirrors)


def test_rename_moves_the_file_and_changes_the_name(profile, store):
    profile.save([CD])
    profile.rename("Paladin")
    assert profile.name == "Paladin"
    assert store.names() == ["Paladin"]
    assert not profile.has_unsaved([CD])


def test_a_failed_rename_keeps_the_old_name(tmp_path):
    profile = ActiveProfile(BrokenStore(tmp_path), "Knight")
    with pytest.raises(OSError, match="disk full"):
        profile.rename("Paladin")
    assert profile.name == "Knight"


def test_delete_removes_the_file(profile, store):
    profile.save([CD])
    profile.delete()
    assert store.names() == []


def test_open_switches_to_a_profile_that_is_not_loaded_yet(profile, store):
    profile.save([CD])
    profile.load(None)
    profile.open("Paladin")
    assert profile.name == "Paladin"
    assert profile.needs_load
    assert not profile.has_unsaved([])


def test_duplicate_writes_the_mirrors_on_screen_to_the_new_profile(profile, store):
    profile.save([CD])
    loaded = profile.load(None)
    changed = [replace(loaded[0], hidden=True)]
    profile.duplicate("Knight copy", changed)
    assert profile.name == "Knight copy"
    assert store.load("Knight copy") == changed
    assert store.load("Knight") == loaded
    assert not profile.has_unsaved(changed)


def test_duplicate_copies_the_file_when_the_mirrors_are_not_loaded(profile, store):
    store.save("Knight", [CD])
    profile.duplicate("Knight copy", [])
    assert profile.name == "Knight copy"
    assert store.load("Knight copy") == [CD]
    assert profile.needs_load


def test_a_failed_duplicate_keeps_the_old_name(tmp_path):
    profile = ActiveProfile(BrokenStore(tmp_path), "Knight")
    profile.load(None)
    with pytest.raises(OSError, match="disk full"):
        profile.duplicate("Knight copy", [CD])
    assert profile.name == "Knight"
