from dataclasses import replace

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.regions import Layout, SavedRegion
from tibia_mirror.services.active_profile import ActiveProfile

CD = SavedRegion("Cooldowns", {"1600x900": Layout(Rect(1, 2, 3, 4), (5, 6))})


def test_a_new_profile_without_mirrors_has_nothing_unsaved():
    assert not ActiveProfile("Knight").has_unsaved([])


def test_a_mirror_that_was_never_saved_is_unsaved():
    assert ActiveProfile("Knight").has_unsaved([CD])


def test_nothing_is_unsaved_right_after_mark_saved():
    profile = ActiveProfile("Knight")
    profile.mark_saved([CD])
    assert not profile.has_unsaved([CD])


def test_a_changed_mirror_is_unsaved():
    profile = ActiveProfile("Knight")
    profile.mark_saved([CD])
    assert profile.has_unsaved([replace(CD, hidden=True)])


def test_a_removed_mirror_is_unsaved():
    profile = ActiveProfile("Knight")
    profile.mark_saved([CD])
    assert profile.has_unsaved([])
