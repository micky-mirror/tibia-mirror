"""Who made the app, since when, and how to reach them: shown in the footer and on About."""

AUTHOR = "micky-mirror"
# Contact on Discord, or None to hide the line.
DISCORD: str | None = "micky.mirror"
# The character that takes Tibia Coin tips, or None to hide the tip lines.
TIP_CHARACTER: str | None = "Micky Mirror"
FIRST_YEAR = 2026


def copyright_years(this_year: int) -> str:
    """The copyright's years: "2026" in the first year, "2026-2027" in the next."""
    return str(FIRST_YEAR) if this_year <= FIRST_YEAR else f"{FIRST_YEAR}-{this_year}"
