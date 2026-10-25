"""Timer alert sounds: Windows' own system sounds, played without blocking."""

import winsound

# mirror_timer.SOUNDS names -> the Windows sound played for them.
ALIASES = {
    "notification": "Notification.Default",
    "critical": "SystemHand",
}
SIMPLE_BEEP = -1  # MessageBeep(0xFFFFFFFF), the plain beep, as winsound's signed int


def play(name: str) -> None:
    """Play the sound named in mirror_timer.SOUNDS ("none" plays nothing).

    A sound Windows refuses (e.g. while audio devices switch) is skipped: the
    caller is the timer loop, which must keep running.
    """
    try:
        if name == "beep":
            winsound.MessageBeep(SIMPLE_BEEP)
        elif name in ALIASES:
            winsound.PlaySound(ALIASES[name], winsound.SND_ALIAS | winsound.SND_ASYNC)
    except RuntimeError:
        pass
