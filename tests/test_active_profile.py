from dataclasses import replace

import pytest

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.profiles import ProfileStore
from tibia_mirror.core.regions import Layout, SavedRegion
from tibia_mirror.services.active_profile import ActiveProfile

CD = SavedRegion("Cooldowns", {"1600x900": Layout(Rect(1, 2, 3, 4), (5, 6))})


class BrokenStore(ProfileStore):
    """A store that cannot write, like a full disk."""

    def save(self, name, saved):
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
