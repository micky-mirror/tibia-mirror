import ast
import pathlib
from types import SimpleNamespace

import pytest

from tibia_mirror.ui.base import scale


def fake_root(tk_scaling):
    """Just enough of a Tk root for scale.init: `tk scaling` is pixels per point."""
    return SimpleNamespace(tk=SimpleNamespace(call=lambda *args: tk_scaling))


@pytest.fixture
def at():
    """Set the display scaling (1.25 for 125%) the way the App does, from Tk."""

    def set_percent(factor):
        scale.init(fake_root(factor * 96 / 72))

    yield set_percent
    set_percent(1.0)


def test_sizes_are_unchanged_at_100_percent(at):
    at(1.0)
    assert scale.factor() == pytest.approx(1.0)
    assert [scale.px(n) for n in (0, 1, 8, 14, 500)] == [0, 1, 8, 14, 500]


def test_sizes_grow_with_the_display_scaling(at):
    at(1.5)
    assert scale.factor() == pytest.approx(1.5)
    assert [scale.px(n) for n in (4, 20, 500, 996)] == [6, 30, 750, 1494]


def test_halves_round_away_from_zero(at):
    at(1.25)
    assert [scale.px(n) for n in (2, 6, 10)] == [3, 8, 13]  # 2.5, 7.5, 12.5
    assert scale.px(-2) == -3


def test_a_size_never_rounds_down_to_nothing(at):
    at(0.25)
    assert scale.px(1) == 1
    assert scale.px(-1) == -1
    assert scale.px(0) == 0


# ---- guard: the app's own pixel sizes go through px() --------------------------

UI = pathlib.Path(__file__).parent.parent / "tibia_mirror" / "ui"
# Keyword arguments that take a size in pixels.
PIXEL_KEYWORDS = {
    *("padx", "pady", "ipadx", "ipady", "width", "height", "wraplength", "minsize"),
    *("radius", "shadow_offset", "shadow_blur"),
}
# Calls whose positional arguments are pixel sizes or coordinates (how many, None: all).
PIXEL_POSITIONALS = {
    "button_pixels": 2,
    "outlined_pixels": 3,
    **dict.fromkeys(("create_line", "create_text", "create_image", "create_window"), None),
    **dict.fromkeys(("create_rectangle", "create_oval", "coords"), None),
}
# Sizes that stay the same at any display scaling, on purpose: (file, code) -> why.
UNSCALED = {
    ("dialogs.py", "padx=dwm.POPUP_FRAME"): "Windows 10's 1px popup border",
    ("dialogs.py", "pady=dwm.POPUP_FRAME"): "Windows 10's 1px popup border",
    ("tooltip.py", "padx=dwm.POPUP_FRAME"): "Windows 10's 1px popup border",
    ("tooltip.py", "pady=dwm.POPUP_FRAME"): "Windows 10's 1px popup border",
    ("loupe.py", "width=self._width - 2"): "the loupe's own 1px frame",
    ("loupe.py", "height=self._height - 2"): "the loupe's own 1px frame",
    ("loupe.py", "padx=1"): "the loupe's own 1px frame",
    ("loupe.py", "pady=1"): "the loupe's own 1px frame",
    ("loupe.py", "self._width // 2 - 1"): "the loupe's own 1px frame",
    ("loupe.py", "self._height - 2 - readout // 2 - px(self.READOUT_LIFT)"): "its 1px frame",
    ("menu.py", "row_height - 2"): "the hover chip leaves 1px above and below",
    ("menu.py", "row[0] + 1"): "the hover chip leaves 1px above and below",
    ("widgets.py", "y + (1 if down else 0)"): "a pressed button sinks 1px, like its image",
    ("about_page.py", "height=1"): "a placeholder: the box is sized once its text is laid out",
    ("settings_page.py", "height=1"): "a placeholder: the card is sized once its rows are drawn",
    ("widgets.py", "height=1"): "a placeholder: the check box is sized to its label",
}


def unscaled_parts(node, parent=None):
    """Bare numbers and CONSTANTS in `node`, outside px() calls.

    Factors and divisors (the 2 in `2 * pad` or `size // 2`) and list indexes aren't
    sizes, so they are left out.
    """
    if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "px":
        return []
    if isinstance(node, ast.Constant):
        number = isinstance(node.value, int | float) and not isinstance(node.value, bool)
        factor = isinstance(parent, ast.BinOp) and isinstance(
            parent.op, ast.Mult | ast.Div | ast.FloorDiv
        )
        return [node] if number and node.value != 0 and not factor else []
    name = getattr(node, "attr", None) or getattr(node, "id", None)
    if isinstance(name, str) and name.isupper() and len(name) > 1:
        return [node]
    if isinstance(node, ast.Attribute):
        return []
    if isinstance(node, ast.Subscript):
        return unscaled_parts(node.value, node)
    return [bad for child in ast.iter_child_nodes(node) for bad in unscaled_parts(child, node)]


def pixel_code(tree):
    """(code, line) of every pixel-size argument in a module's syntax tree."""
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg in PIXEL_KEYWORDS:
            yield f"{node.arg}={ast.unparse(node.value)}", node.value
        elif isinstance(node, ast.Call):
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in PIXEL_POSITIONALS:
                for arg in node.args[: PIXEL_POSITIONALS[name]]:
                    yield ast.unparse(arg), arg


def test_ui_sizes_scale_with_the_display():
    """A size written as a plain number or constant stays 100% sized at 125% or 150%.

    Wrap it in px(); if it must stay the same on purpose, add it to UNSCALED with why.
    """
    found = set()
    problems = []
    for path in sorted(UI.rglob("*.py")):
        for code, node in pixel_code(ast.parse(path.read_text(encoding="utf-8"))):
            if unscaled_parts(node):
                found.add((path.name, code))
                if (path.name, code) not in UNSCALED:
                    problems.append(f"{path.name}:{node.lineno}: {code}")
    assert problems == []
    assert set(UNSCALED) - found == set(), "UNSCALED lists code that no longer exists"
