from tibia_mirror.config import FRAME_COLORS
from tibia_mirror.core.regions import next_default_name
from tibia_mirror.ui.base.theme import FRAME_COLOR_HEX


def test_next_default_name_fills_the_lowest_gap():
    assert next_default_name([]) == "Region 1"
    assert next_default_name(["Region 1", "Region 2"]) == "Region 3"
    assert next_default_name(["Region 1", "Cooldowns", "Region 3"]) == "Region 2"


def test_next_default_name_takes_a_stem_and_ignores_case():
    assert next_default_name(["profile 1"], stem="Profile") == "Profile 2"


def test_every_frame_colour_has_a_colour_to_draw():
    assert set(FRAME_COLORS) - {"default"} == set(FRAME_COLOR_HEX)
    assert len(FRAME_COLORS) == len(set(FRAME_COLORS))
