import hashlib
import math

import pytest

from tibia_mirror.ui.base.render import (
    Box,
    ButtonStyle,
    Margins,
    button_pixels,
    hex_to_rgb,
    margins,
    outlined_pixels,
)

BG = "#1e1e2e"
FILL = "#89b4fa"
FLAT = ButtonStyle(fill=FILL, radius=6)
SHADOWED = ButtonStyle(fill=FILL, radius=6, shadow_alpha=0.5, shadow_offset=3, shadow_blur=8)


def luminance(color):
    return sum(hex_to_rgb(color))


def test_no_shadow_means_no_margins():
    assert margins(FLAT) == Margins(0, 0, 0, 0)


def test_shadow_margins_extend_further_below():
    assert margins(SHADOWED) == Margins(left=8, top=5, right=8, bottom=11)


BOX = Box(0, 0, 100, 40, radius=6)


def test_box_distance_is_below_zero_inside_and_above_zero_outside():
    assert BOX.distance(50, 20) < 0  # the middle
    assert BOX.distance(150, 20) > 0  # far to the right
    assert BOX.distance(100, 20) == pytest.approx(0)  # on the right edge


def test_box_distance_follows_the_rounded_corner():
    # the corner point of the frame lies outside the curve, by the diagonal minus the radius
    assert BOX.distance(0, 0) == pytest.approx(6 * math.sqrt(2) - 6)


def test_straight_rows_start_below_the_rounded_corners():
    assert not BOX.is_straight_row(5.5)  # the last row of the top corners
    assert BOX.is_straight_row(6.5)
    assert BOX.is_straight_row(33.5)
    assert not BOX.is_straight_row(34.5)  # the first row of the bottom corners


def test_moved_down_keeps_the_size():
    assert BOX.moved_down(3) == Box(0, 3, 100, 43, radius=6)


def test_image_size_includes_margins():
    rows = button_pixels(40, 20, SHADOWED, BG)
    assert len(rows) == 5 + 20 + 11
    assert all(len(r) == 8 + 40 + 8 for r in rows)


def test_centre_is_fill_and_corners_are_rounded_away():
    rows = button_pixels(40, 20, FLAT, BG)
    assert rows[10][20] == FILL
    assert rows[0][0] == BG  # outside the rounded corner
    assert rows[0][20] == FILL  # straight top edge is fully covered


def test_edges_are_antialiased():
    rows = button_pixels(40, 20, FLAT, BG)
    corner_band = {rows[1][1], rows[0][2], rows[2][0]}
    assert corner_band - {BG, FILL}, "expected blended pixels along the rounded corner"


def test_shadow_darkens_below_but_not_above():
    rows = button_pixels(40, 20, SHADOWED, BG)
    m = margins(SHADOWED)
    below = rows[m.top + 20 + 2][m.left + 20]
    above = rows[0][m.left + 20]
    assert luminance(below) < luminance(BG)
    assert luminance(above) <= luminance(BG)
    assert luminance(below) < luminance(above)


def test_pressed_moves_body_down_one_pixel():
    m = margins(SHADOWED)
    normal = button_pixels(40, 20, SHADOWED, BG)
    pressed = button_pixels(40, 20, SHADOWED, BG, pressed=True)
    x = m.left + 20
    assert normal[m.top][x] == FILL
    assert pressed[m.top][x] != FILL
    assert pressed[m.top + 1][x] == FILL


def test_outlined_box_has_a_one_pixel_border():
    rows = outlined_pixels(40, 20, 6, "#313244", "#89b4fa", BG)
    assert len(rows) == 20 and len(rows[0]) == 40
    assert rows[0][0] == BG  # rounded corner
    assert rows[0][20] == "#89b4fa"  # top edge
    assert rows[10][0] == "#89b4fa"  # left edge
    assert rows[10][20] == "#313244"  # inside


def test_outlined_box_corners_stay_background_outside_the_curve():
    """The fill's own corners must not paint border colour outside the rounded outline."""
    rows = outlined_pixels(40, 36, 8, "#313244", "#89b4fa", BG)
    for y, x in ((1, 1), (1, 38), (34, 1), (34, 38)):
        assert rows[y][x] == BG


def fingerprint(rows):
    """A short hash of every pixel: one changed pixel changes it."""
    text = "\n".join(" ".join(row) for row in rows)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


PRIMARY = ButtonStyle("#89b4fa", radius=10, shadow_alpha=0.55, shadow_offset=4, shadow_blur=10)
SECONDARY_LIGHT = ButtonStyle(
    "#ffffff", radius=10, shadow_alpha=0.2025, shadow_offset=3, shadow_blur=8
)
KNOB = ButtonStyle("#cdd6f4", radius=9, shadow_alpha=0.45, shadow_offset=1, shadow_blur=4)
WIDE_SHADOW = ButtonStyle("#89b4fa", radius=15, shadow_alpha=0.55, shadow_offset=5, shadow_blur=13)


# Real looks of the app at 100% and 125%, and two odd shapes, pinned before the rewrite.
@pytest.mark.parametrize(
    ("width", "height", "style", "background", "pressed", "expected"),
    [
        (120, 34, PRIMARY, "#1e1e2e", False, "49e6b02590f8b2f4"),
        (120, 34, PRIMARY, "#1e1e2e", True, "0238f16824750017"),
        (95, 38, SECONDARY_LIGHT, "#eff1f5", False, "95c071b86de41d58"),
        (95, 38, SECONDARY_LIGHT, "#eff1f5", True, "2097618ceaffd099"),
        (18, 18, KNOB, "#313244", False, "7b79cb1fd1714e1e"),
        (8, 60, ButtonStyle("#45475a", radius=4), "#1e1e2e", False, "916b2b88c47e7f95"),
        (30, 5, ButtonStyle("#89b4fa", radius=0), "#1e1e2e", False, "c20a55589bfe753b"),
        (57, 83, WIDE_SHADOW, "#1e1e2e", True, "55bbc6d75ef56cb2"),
        (6, 3, ButtonStyle("#89b4fa", radius=15), "#1e1e2e", False, "6e81736e8985893a"),
    ],
)
def test_button_pixels_stay_the_same(width, height, style, background, pressed, expected):
    assert fingerprint(button_pixels(width, height, style, background, pressed)) == expected


@pytest.mark.parametrize(
    ("width", "height", "radius", "fill", "border", "background", "expected"),
    [
        (200, 30, 6, "#313244", "#89b4fa", "#1e1e2e", "48f471ff632e573e"),
        (20, 20, 3, "#f38ba8", "#f38ba8", "#1e1e2e", "2dd49ba3a7363afd"),
        (45, 45, 10, "#ffffff", "#bcc0cc", "#eff1f5", "153b38e046945a84"),
    ],
)
def test_outlined_pixels_stay_the_same(width, height, radius, fill, border, background, expected):
    assert fingerprint(outlined_pixels(width, height, radius, fill, border, background)) == expected


def test_custom_widgets_do_not_overwrite_tkinter_internals():
    """E.g. `self._name` is Tk's own name for a widget; replacing it breaks destroy()."""
    import ast
    import pathlib
    import tkinter as tk

    reserved = set(dir(tk.Canvas)) | set(dir(tk.Frame)) | {"_w", "_name", "children", "master"}
    clashes = []
    for path in (pathlib.Path(__file__).parent.parent / "tibia_mirror" / "ui").rglob("*.py"):
        for cls in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(cls, ast.ClassDef):
                continue
            if not {ast.unparse(b) for b in cls.bases} & {"tk.Canvas", "tk.Frame"}:
                continue
            for node in ast.walk(cls):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.ctx, ast.Store)
                    and ast.unparse(node.value) == "self"
                    and node.attr in reserved
                ):
                    clashes.append(f"{path.name}:{node.lineno} {cls.name}.{node.attr}")
    assert clashes == []
