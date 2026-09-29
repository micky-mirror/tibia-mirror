import pathlib
import re

from tibia_mirror import __version__
from tibia_mirror.about import FIRST_YEAR, copyright_years

PYPROJECT = pathlib.Path(__file__).parent.parent / "pyproject.toml"


def test_first_year_alone():
    assert FIRST_YEAR == 2026
    assert copyright_years(2026) == "2026"


def test_later_years_as_a_range():
    assert copyright_years(2027) == "2026-2027"
    assert copyright_years(2031) == "2026-2031"


def test_a_clock_set_back_still_shows_the_first_year():
    assert copyright_years(2025) == "2026"


def test_about_page_version_matches_the_package():
    # The About page shows __version__; pyproject.toml must say the same.
    match = re.search(r'^version = "(.+)"$', PYPROJECT.read_text(encoding="utf-8"), re.MULTILINE)
    assert match is not None
    assert match.group(1) == __version__
