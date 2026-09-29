"""Links from Tibia characters to profiles, and the character in Tibia's window title.

Names compare ignoring case. Links are sorted (character, profile) pairs, so
they fit in the frozen Settings.
"""

from collections.abc import Iterable

from tibia_mirror.profiles import copy_name, name_error

Links = tuple[tuple[str, str], ...]

TITLE_PREFIX = "Tibia - "


def character_in_title(title: str) -> str | None:
    """The logged-in character's name from Tibia's window title, or None on the login screen."""
    if not title.startswith(TITLE_PREFIX):
        return None
    return title[len(TITLE_PREFIX) :].strip() or None


def profile_of(links: Links, character: str) -> str | None:
    key = character.casefold()
    return next((profile for linked, profile in links if linked.casefold() == key), None)


def spelling(links: Links, character: str) -> str:
    """The character's name as it was linked, or as given if it is not linked."""
    key = character.casefold()
    return next((linked for linked, _profile in links if linked.casefold() == key), character)


def characters_of(links: Links, profile: str) -> list[str]:
    key = profile.casefold()
    return [linked for linked, linked_profile in links if linked_profile.casefold() == key]


def link(links: Links, character: str, profile: str) -> Links:
    """`character` opens `profile` from now on, instead of any profile it opened before."""
    return _sorted([*unlink(links, character), (character, profile)])


def unlink(links: Links, character: str) -> Links:
    key = character.casefold()
    return tuple((linked, profile) for linked, profile in links if linked.casefold() != key)


def rename_profile(links: Links, old: str, new: str) -> Links:
    key = old.casefold()
    return tuple(
        (linked, new if profile.casefold() == key else profile) for linked, profile in links
    )


def drop_profile(links: Links, profile: str) -> Links:
    key = profile.casefold()
    return tuple((linked, other) for linked, other in links if other.casefold() != key)


def profile_for_new_character(
    character: str, names: Iterable[str], links: Links, suffix: str = "copy"
) -> tuple[str, bool]:
    """(profile, whether it exists) for a character's first login.

    An unused profile with the character's name is reused; otherwise a new one is
    named after the character, plus `suffix` if that name is taken.
    """
    names = list(names)
    key = character.casefold()
    same = next((name for name in names if name.casefold() == key), None)
    if same is not None and not characters_of(links, same):
        return same, True
    if name_error(character, names) is None:
        return character, False
    return copy_name(character, names, suffix), False


def character_error(name: str) -> str | None:
    """Why `name` (already stripped) can't be a character's name, or None if it can."""
    return "Enter a name" if not name else None


def from_json(data: object) -> Links:
    """Links from settings.json's {"character": "profile"}; anything else is dropped."""
    if not isinstance(data, dict):
        return ()
    pairs: Links = ()
    for character, profile in data.items():
        if isinstance(profile, str) and profile and character.strip():
            pairs = link(pairs, character.strip(), profile)
    return pairs


def to_json(links: Links) -> dict[str, str]:
    return dict(links)


def _sorted(pairs: Iterable[tuple[str, str]]) -> Links:
    return tuple(sorted(pairs, key=lambda pair: pair[0].casefold()))
