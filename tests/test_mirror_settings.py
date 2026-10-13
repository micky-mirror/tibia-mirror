"""Reading the settings of a mirror from a profile file, and writing them back."""

import pytest

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.regions import Layout

# One layout as a profile file holds it, and the same layout as the class holds it.
LAYOUTS_JSON = {"1920x1080": {"region": [10, 20, 300, 40], "offset": [5, 6]}}
LAYOUTS = {"1920x1080": Layout(Rect(10, 20, 300, 40), (5, 6))}


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
