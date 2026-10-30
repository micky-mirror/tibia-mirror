"""The character logged in to Tibia, read from the title of its window."""

TITLE_PREFIX = "Tibia - "


def character_in_title(title: str) -> str | None:
    """The logged-in character's name from Tibia's window title, or None on the login screen."""
    if not title.startswith(TITLE_PREFIX):
        return None
    return title[len(TITLE_PREFIX) :].strip() or None
