"""Profiles: named sets of mirrors, one JSON file each.

Names are file names, so they follow Windows' rules and compare ignoring case.
"""

import shutil
from collections.abc import Iterable
from pathlib import Path

from tibia_mirror import regions
from tibia_mirror.config import DEFAULT_PROFILE
from tibia_mirror.geometry import Rect

INVALID_CHARS = frozenset('<>:"/\\|?*')
RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"{port}{number}" for port in ("COM", "LPT") for number in range(1, 10)}
)


def name_error(name: str, taken: Iterable[str]) -> str | None:
    """Why `name` can't be a profile name, or None.

    `taken` leaves out the profile being renamed, so a case-only rename is fine.
    """
    if not name:
        return "Enter a name"
    if any(char in INVALID_CHARS or ord(char) < 32 for char in name):
        return "A name can't contain < > : \" / \\ | ? *"
    if name.endswith((".", " ")):
        return "A name can't end with a dot or a space"
    if name.split(".")[0].strip().upper() in RESERVED_NAMES:
        return "That name is reserved by Windows"
    if name.casefold() in {other.casefold() for other in taken}:
        return "A profile with this name already exists"
    return None


def copy_name(name: str, taken: Iterable[str], suffix: str = "copy") -> str:
    """First free "<name> copy", "<name> copy 2", ... for a duplicate (`suffix` is "copy")."""
    taken = {other.casefold() for other in taken}
    candidate, number = f"{name} {suffix}", 1
    while candidate.casefold() in taken:
        number += 1
        candidate = f"{name} {suffix} {number}"
    return candidate


class ProfileStore:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def _path(self, name: str) -> Path:
        return self.folder / f"{name}.json"

    def names(self) -> list[str]:
        if not self.folder.is_dir():
            return []
        return sorted((file.stem for file in self.folder.glob("*.json")), key=str.casefold)

    def load(self, name: str, client: Rect | None = None) -> list[regions.SavedRegion]:
        """The profile's regions (none if its file is gone); `client` reads pre-layout files."""
        path = self._path(name)
        return regions.load(path, client) if path.exists() else []

    def copy(self, source: str, target: str) -> None:
        """Duplicate a profile's file byte for byte."""
        shutil.copyfile(self._path(source), self._path(target))

    def export(self, name: str, target: Path) -> None:
        """Copy a profile's file, as last saved, to `target` (any path)."""
        shutil.copyfile(self._path(name), target)

    def save(self, name: str, saved: Iterable[regions.SavedRegion]) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)
        regions.save(self._path(name), saved)

    def rename(self, old: str, new: str) -> None:
        self._path(old).rename(self._path(new))

    def delete(self, name: str) -> None:
        self._path(name).unlink(missing_ok=True)

    def ensure_one(self) -> None:
        """Make sure a profile exists: an empty Default the first time."""
        if not self.names():
            self.save(DEFAULT_PROFILE, [])
