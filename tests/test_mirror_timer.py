"""The timer of a mirror: reading it from a profile file and writing it back."""

import pytest

from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.core.timers import TimerSettings

# A timer where every value is different from its default.
CHANGED_TIMER = MirrorTimer(
    is_on=True,
    alert_seconds=90,
    direction="up",
    key=(120, ("shift",)),
    sound="beep",
    is_paused_offline=False,
)


def test_a_missing_timer_gives_the_defaults():
    assert MirrorTimer.from_json(None) == MirrorTimer()


def test_a_saved_timer_is_read():
    data = {
        "enabled": True,
        "alert": 90,
        "direction": "up",
        "key": 120,
        "modifiers": ["shift"],
        "sound": "beep",
        "offline_pause": False,
    }

    assert MirrorTimer.from_json(data) == CHANGED_TIMER


def test_wrong_values_become_the_defaults():
    data = {
        "enabled": "yes",
        "alert": 0,
        "direction": "sideways",
        "key": 999,
        "modifiers": ["shift"],
        "sound": "trumpet",
        "offline_pause": 1,
    }

    assert MirrorTimer.from_json(data) == MirrorTimer()


@pytest.mark.parametrize("sound", ["asterisk", "exclamation"])
def test_a_removed_sound_becomes_the_default_sound(sound):
    assert MirrorTimer.from_json({"sound": sound}).sound == MirrorTimer().sound


def test_a_written_timer_is_read_back_the_same():
    assert MirrorTimer.from_json(CHANGED_TIMER.to_json()) == CHANGED_TIMER


def test_the_old_timer_class_reads_and_writes_the_same_file():
    file_content = CHANGED_TIMER.to_json()

    old_file_content = TimerSettings.from_json(file_content).to_json()
    # only the old app still lets other mouse buttons than the left one start a timer
    del old_file_content["button"]

    assert old_file_content == file_content
