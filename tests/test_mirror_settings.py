"""Reading the settings of a mirror from a profile file, and writing them back."""

import json

import pytest

from tibia_mirror.config import ZOOM_RANGE
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.core.regions import Layout, SavedRegion

# One layout as a profile file holds it, and the same layout as the class holds it.
LAYOUTS_JSON = {"1920x1080": {"region": [10, 20, 300, 40], "offset": [5, 6]}}
LAYOUTS = {"1920x1080": Layout(Rect(10, 20, 300, 40), (5, 6))}

# The three values a mirror must have, as a profile file holds them.
REQUIRED_JSON = {"id": "mirror-1", "name": "Minimap", "layouts": LAYOUTS_JSON}

# A mirror where every value is different from its default.
CHANGED_MIRROR = MirrorSettings(
    mirror_id="mirror-1",
    name="Minimap",
    layouts=LAYOUTS,
    opacity=0.8,
    zoom=2.0,
    colour="blue",
    is_hidden=True,
    is_locked=True,
    timer=MirrorTimer(is_on=True, alert_seconds=30),
)


def test_id_name_and_layouts_are_read() -> None:
    data = {"id": "mirror-1", "name": "Minimap", "layouts": LAYOUTS_JSON}

    mirror = MirrorSettings.from_json(data)

    assert mirror.mirror_id == "mirror-1"
    assert mirror.name == "Minimap"
    assert mirror.layouts == LAYOUTS


def test_a_mirror_without_an_id_gets_a_new_one() -> None:
    data = {"name": "Minimap", "layouts": LAYOUTS_JSON}

    first = MirrorSettings.from_json(data)
    second = MirrorSettings.from_json(data)

    assert first.mirror_id != ""
    assert first.mirror_id != second.mirror_id


def test_a_mirror_without_a_name_is_refused() -> None:
    with pytest.raises(ValueError):
        MirrorSettings.from_json({"layouts": LAYOUTS_JSON})


def test_a_mirror_without_layouts_is_refused() -> None:
    with pytest.raises(ValueError):
        MirrorSettings.from_json({"name": "Minimap"})


def test_a_layout_for_a_window_size_of_zero_is_left_out() -> None:
    layouts = LAYOUTS_JSON | {"0x0": {"region": [0, 0, 1, 1]}}

    mirror = MirrorSettings.from_json({"name": "Minimap", "layouts": layouts})

    assert mirror.layouts == LAYOUTS


def test_content_that_is_not_an_object_is_refused() -> None:
    with pytest.raises(ValueError):
        MirrorSettings.from_json([1, 2])


def test_missing_values_get_their_defaults() -> None:
    mirror = MirrorSettings.from_json(REQUIRED_JSON)

    assert mirror == MirrorSettings(mirror_id="mirror-1", name="Minimap", layouts=LAYOUTS)


def test_saved_values_are_read() -> None:
    data = REQUIRED_JSON | {
        "opacity": 0.8,
        "zoom": 2.0,
        "color": "blue",
        "hidden": True,
        "locked": True,
        "timer": {"enabled": True, "alert": 30},
    }

    assert MirrorSettings.from_json(data) == CHANGED_MIRROR


def test_opacity_and_zoom_are_moved_into_the_allowed_range() -> None:
    mirror = MirrorSettings.from_json(REQUIRED_JSON | {"opacity": 5, "zoom": 100})

    assert mirror.opacity == 1.0
    assert mirror.zoom == ZOOM_RANGE[1]


def test_wrong_values_get_their_defaults() -> None:
    data = REQUIRED_JSON | {
        "opacity": True,
        "zoom": "big",
        "color": "pink",
        "hidden": 1,
        "locked": "yes",
        "timer": "soon",
    }

    mirror = MirrorSettings.from_json(data)

    assert mirror == MirrorSettings(mirror_id="mirror-1", name="Minimap", layouts=LAYOUTS)


def test_written_settings_are_read_back_the_same() -> None:
    file_content = json.loads(json.dumps(CHANGED_MIRROR.to_json()))

    assert MirrorSettings.from_json(file_content) == CHANGED_MIRROR


def test_the_old_class_reads_and_writes_the_same_file() -> None:
    file_content = CHANGED_MIRROR.to_json()

    old_file_content = SavedRegion.from_json(file_content, default_name="").to_json()
    # only the old app still lets other mouse buttons than the left one start a timer
    del old_file_content["timer"]["button"]

    assert old_file_content == file_content
