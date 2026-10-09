import json
from dataclasses import replace

import pytest

from tibia_mirror.config import (
    DEFAULT_MIRROR_POS,
    DEFAULT_OPACITY,
    FRAME_COLORS,
    MIN_OPACITY,
    ZOOM_RANGE,
)
from tibia_mirror.core import regions
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.regions import Layout, SavedRegion, guess_layout, next_default_name, size_key
from tibia_mirror.core.timers import TimerSettings
from tibia_mirror.ui.theme import FRAME_COLOR_HEX

WINDOWED = size_key(1600, 900)
CLIENT = Rect(100, 50, 1600, 900)  # the client area on screen


def region(name="Cooldowns", **kw):
    return SavedRegion(name, {WINDOWED: Layout(Rect(1, 2, 3, 4), (5, 6))}, **kw)


def test_round_trip(tmp_path):
    path = tmp_path / "profile.json"
    saved = [
        region(),
        SavedRegion(
            "Minimap",
            {
                WINDOWED: Layout(Rect(1208, 1255, 63, 59), (-500, 10)),
                size_key(1920, 1080): Layout(Rect(1500, 20, 63, 59), (40, 40)),
            },
            opacity=0.75,
            hidden=True,
            locked=True,
            zoom=2.5,
            color="teal",
            timer=TimerSettings(enabled=True, alert=90, direction="up", button="right", key=116),
        ),
    ]
    regions.save(path, saved)
    assert regions.load(path) == saved


def test_file_format_is_stable(tmp_path):
    path = tmp_path / "profile.json"
    regions.save(path, [region("Region 1")])
    assert json.loads(path.read_text()) == {
        "version": 2,
        "mirrors": [
            {
                "name": "Region 1",
                "opacity": 0.5,
                "zoom": 1.0,
                "color": "default",
                "timer": {
                    "enabled": False,
                    "alert": 60,
                    "direction": "down",
                    "button": "both",
                    "key": None,
                    "modifiers": [],
                    "sound": "asterisk",
                    "offline_pause": True,
                },
                "hidden": False,
                "locked": False,
                "layouts": {"1600x900": {"region": [1, 2, 3, 4], "offset": [5, 6]}},
            }
        ],
    }


def test_pre_layout_files_become_a_layout_for_the_current_client(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(
        json.dumps(
            [
                {"name": "CD", "region": [1, 2, 3, 4], "pos": [300, 250], "opacity": 0.7},
                {"region": [5, 6, 7, 8]},
            ]
        )
    )
    loaded = regions.load(path, client=CLIENT)
    assert loaded[0].layouts == {WINDOWED: Layout(Rect(1, 2, 3, 4), (200, 200))}
    assert loaded[0].opacity == 0.7
    assert loaded[1].name == "Region 2"
    px, py = DEFAULT_MIRROR_POS
    assert loaded[1].layouts[WINDOWED].offset == (px - CLIENT.x, py - CLIENT.y)
    assert loaded[1].opacity == DEFAULT_OPACITY
    assert loaded[1].zoom == 1.0
    assert not (loaded[1].hidden or loaded[1].locked)


def test_pre_layout_files_need_the_client(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(json.dumps([{"region": [1, 2, 3, 4]}]))
    with pytest.raises(ValueError):
        regions.load(path)


def test_zoom_is_clamped(tmp_path):
    path = tmp_path / "profile.json"
    layouts = {WINDOWED: {"region": [1, 2, 3, 4]}}
    path.write_text(
        json.dumps({"mirrors": [{"layouts": layouts, "zoom": z} for z in (0.01, 1.5, 99)]})
    )
    assert [r.zoom for r in regions.load(path)] == [ZOOM_RANGE[0], 1.5, ZOOM_RANGE[1]]


def test_opacity_is_clamped(tmp_path):
    path = tmp_path / "profile.json"
    layouts = {WINDOWED: {"region": [1, 2, 3, 4]}}
    path.write_text(
        json.dumps(
            {
                "version": 2,
                "mirrors": [
                    {"layouts": layouts, "opacity": 0.75},
                    {"layouts": layouts, "opacity": 0.0},
                    {"layouts": layouts, "opacity": 7},
                ],
            }
        )
    )
    assert [r.opacity for r in regions.load(path)] == [0.75, MIN_OPACITY, 1.0]


def test_bad_layout_keys_and_empty_layouts_are_rejected(tmp_path):
    path = tmp_path / "profile.json"
    for layouts in ({"big": {"region": [1, 2, 3, 4]}}, {}):
        path.write_text(json.dumps({"mirrors": [{"layouts": layouts}]}))
        with pytest.raises(ValueError):
            regions.load(path)


def test_guess_keeps_the_region_size_and_moves_it_proportionally():
    layouts = {WINDOWED: Layout(Rect(790, 440, 20, 20), (1600, 0))}
    guess = guess_layout(layouts, 3200, 1800)
    assert guess.region == Rect(1590, 890, 20, 20)  # centre 800,450 -> 1600,900
    assert guess.offset == (3200, 0)


def test_guess_starts_from_the_closest_known_size_and_stays_inside():
    layouts = {
        size_key(800, 600): Layout(Rect(0, 0, 10, 10), (0, 0)),
        size_key(1900, 1000): Layout(Rect(1880, 980, 20, 20), (7, 7)),
    }
    guess = guess_layout(layouts, 1920, 1080)
    assert guess.offset == (7, 8)
    assert guess.region.right <= 1920 and guess.region.bottom <= 1080


def test_next_default_name_fills_the_lowest_gap():
    assert next_default_name([]) == "Region 1"
    assert next_default_name(["Region 1", "Region 2"]) == "Region 3"
    assert next_default_name(["Region 1", "Cooldowns", "Region 3"]) == "Region 2"


def test_next_default_name_takes_a_stem_and_ignores_case():
    assert next_default_name(["profile 1"], stem="Profile") == "Profile 2"


def test_snapshot_ignores_float_noise_below_stored_precision():
    assert regions.snapshot([region(opacity=0.1 + 0.2)]) == regions.snapshot([region(opacity=0.3)])


def test_snapshot_sees_every_kind_of_change():
    base = region()
    moved = replace(base, layouts={WINDOWED: Layout(Rect(1, 2, 3, 4), (9, 9))})
    for changed in (
        replace(base, name="Spells"),
        replace(base, hidden=True),
        replace(base, locked=True),
        replace(base, zoom=2.0),
        replace(base, color="red"),
        moved,
    ):
        assert regions.snapshot([changed]) != regions.snapshot([base])


def test_a_zero_size_client_never_becomes_a_layout(tmp_path):
    # Windows reports a minimized window's client area as 0 x 0.
    path = tmp_path / "old.json"
    path.write_text(json.dumps([{"region": [1, 2, 3, 4], "pos": [5, 6]}]))
    with pytest.raises(ValueError):
        regions.load(path, client=Rect(0, 0, 0, 0))
    path.write_text(json.dumps({"mirrors": [{"layouts": {"0x0": {"region": [1, 2, 3, 4]}}}]}))
    with pytest.raises(ValueError):
        regions.load(path)


def test_bad_layouts_are_skipped_and_the_rest_kept(tmp_path):
    path = tmp_path / "profile.json"
    good = {"region": [1, 2, 3, 4], "offset": [5, 6]}
    path.write_text(json.dumps({"mirrors": [{"layouts": {"0x0": good, WINDOWED: good}}]}))
    assert list(regions.load(path)[0].layouts) == [WINDOWED]


def test_unknown_frame_colours_fall_back_to_default(tmp_path):
    path = tmp_path / "profile.json"
    layouts = {WINDOWED: {"region": [1, 2, 3, 4]}}
    path.write_text(json.dumps({"mirrors": [{"layouts": layouts, "color": "pink"}]}))
    assert regions.load(path)[0].color == "default"


def test_every_frame_colour_has_a_colour_to_draw():
    assert set(FRAME_COLORS) - {"default"} == set(FRAME_COLOR_HEX)
    assert len(FRAME_COLORS) == len(set(FRAME_COLORS))


def test_a_mirror_id_is_saved_first_and_read_back(tmp_path):
    path = tmp_path / "profile.json"
    regions.save(path, [region(id="abc123")])
    assert next(iter(json.loads(path.read_text())["mirrors"][0])) == "id"
    assert regions.load(path)[0].id == "abc123"


def test_assign_ids_gives_missing_ones_and_keeps_the_rest():
    with_ids, missing = regions.assign_ids([region(id="keep"), region()])
    assert missing
    assert with_ids[0].id == "keep"
    assert with_ids[1].id not in ("", "keep")
    assert regions.assign_ids(with_ids) == (with_ids, False)
