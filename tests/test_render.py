from tibia_mirror.ui.base.render import (
    ButtonStyle,
    Margins,
    button_pixels,
    coverage,
    hex_to_rgb,
    margins,
    mix,
    outlined_pixels,
    rgb_to_hex,
    rounded_rect_distance,
    shadow_opacity,
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


def test_distance_sign():
    assert rounded_rect_distance(50, 20, 0, 0, 100, 40, 6) < 0  # centre
    assert rounded_rect_distance(150, 20, 0, 0, 100, 40, 6) > 0  # far right
    assert abs(rounded_rect_distance(100, 20, 0, 0, 100, 40, 6)) < 1e-9  # on the edge


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


def every_pixel_button(width, height, style, background, pressed=False):
    """button_pixels without reusing rows: each pixel computed on its own."""
    m = margins(style)
    sink = 1 if pressed else 0
    x0, y0 = m.left, m.top + sink
    x1, y1 = x0 + width, y0 + height
    drop = (style.shadow_offset // 2 if pressed else style.shadow_offset) - sink
    alpha = style.shadow_alpha * (0.6 if pressed else 1.0)
    rows = []
    for y in range(m.top + height + m.bottom):
        row = []
        for x in range(m.left + width + m.right):
            cx, cy = x + 0.5, y + 0.5
            color = hex_to_rgb(background)
            if alpha:
                shadow_box = (x0, y0 + drop, x1, y1 + drop)
                to_shadow = rounded_rect_distance(cx, cy, *shadow_box, style.radius)
                color = mix(color, (0, 0, 0), alpha * shadow_opacity(to_shadow, style.shadow_blur))
            body = coverage(rounded_rect_distance(cx, cy, x0, y0, x1, y1, style.radius))
            if body:
                color = mix(color, hex_to_rgb(style.fill), body)
            row.append(rgb_to_hex(color))
        rows.append(tuple(row))
    return tuple(rows)


def every_pixel_outlined(width, height, radius, fill, border, background):
    """outlined_pixels without reusing rows."""
    rows = []
    for y in range(height):
        row = []
        for x in range(width):
            cx, cy = x + 0.5, y + 0.5
            outer = coverage(rounded_rect_distance(cx, cy, 0, 0, width, height, radius))
            color = mix(hex_to_rgb(background), hex_to_rgb(border), outer)
            inner_radius = max(0, radius - 1)
            inner = coverage(
                rounded_rect_distance(cx, cy, 1, 1, width - 1, height - 1, inner_radius)
            )
            row.append(rgb_to_hex(mix(color, hex_to_rgb(fill), inner)))
        rows.append(tuple(row))
    return tuple(rows)


def test_reused_middle_rows_match_computing_every_pixel():
    styles = (
        FLAT,
        SHADOWED,
        ButtonStyle(fill=FILL, radius=0),
        ButtonStyle(fill=FILL, radius=15),  # a pill: no straight middle at all
        ButtonStyle(fill=FILL, radius=10, shadow_alpha=0.55, shadow_offset=5, shadow_blur=13),
    )
    for style in styles:
        for width, height in ((40, 30), (57, 83), (6, 3)):
            for pressed in (False, True):
                expected = every_pixel_button(width, height, style, BG, pressed)
                assert button_pixels(width, height, style, BG, pressed) == expected
    for width, height, radius in ((40, 36, 8), (45, 45, 10), (20, 5, 3), (30, 50, 0)):
        expected = every_pixel_outlined(width, height, radius, "#313244", FILL, BG)
        assert outlined_pixels(width, height, radius, "#313244", FILL, BG) == expected


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
