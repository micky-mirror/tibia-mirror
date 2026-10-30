"""Profile names. They are file names, so they follow Windows' rules and compare ignoring case."""

from collections.abc import Iterable

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
