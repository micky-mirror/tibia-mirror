import pytest

from tibia_mirror.tibia import is_tibia_client

CLIENT_EXE = r"C:\Users\Player\AppData\Local\Tibia\packages\Tibia\bin\client.exe"


@pytest.mark.parametrize("title", ["Tibia", "Tibia - Knight Name"])
def test_matches_real_client(title):
    assert is_tibia_client(title, CLIENT_EXE)


def test_exe_match_is_case_insensitive():
    assert is_tibia_client("Tibia", CLIENT_EXE.upper())


@pytest.mark.parametrize(
    ("title", "exe"),
    [
        # Title collisions that must not match.
        ("TibiaMirror - main.py", r"C:\Program Files\JetBrains\bin\pycharm64.exe"),
        ("Tibia Mirror", r"C:\Python310\python.exe"),
        # Right exe, but not a Tibia titled window (e.g. a helper window).
        ("Qt tool window", CLIENT_EXE),
        # Process path unreadable.
        ("Tibia", ""),
        # Some other game's client.exe.
        ("Tibia", r"C:\Games\Other\bin\client.exe"),
    ],
)
def test_rejects_non_client_windows(title, exe):
    assert not is_tibia_client(title, exe)
