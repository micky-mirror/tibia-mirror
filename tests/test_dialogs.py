from types import SimpleNamespace

from tibia_mirror.ui.controls.dialogs import fit_name

FONT = SimpleNamespace(measure=len)  # one pixel per character
TEMPLATE = 'Timer for "{name}"'


def test_a_name_that_fits_is_shown_whole():
    assert fit_name(TEMPLATE, "Amulets", FONT, 40) == 'Timer for "Amulets"'


def test_a_long_name_is_cut_short_inside_the_title():
    assert (
        fit_name(TEMPLATE, "M_LVL Food with a long name", FONT, 25) == 'Timer for "M_LVL Food w…"'
    )
