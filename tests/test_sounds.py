import pytest

from tibia_mirror import sounds


def _refuse(*_args):
    raise RuntimeError("Failed to play sound")  # what winsound raises when Windows refuses


@pytest.mark.parametrize("name", ["beep", "asterisk", "notification", "none"])
def test_a_sound_windows_refuses_is_skipped(monkeypatch, name):
    # A raised error would escape the timer loop and freeze every timer.
    monkeypatch.setattr(sounds.winsound, "MessageBeep", _refuse)
    monkeypatch.setattr(sounds.winsound, "PlaySound", _refuse)
    sounds.play(name)
