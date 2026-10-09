import ast
import pathlib
import string

import pytest

from tibia_mirror import i18n
from tibia_mirror.i18n import POLISH, POLISH_PLURALS, tr, tr_n

SOURCE = pathlib.Path(__file__).parent.parent / "tibia_mirror"


@pytest.fixture(autouse=True)
def english_afterwards():
    yield
    i18n.use("en")


def test_english_is_the_text_itself_with_fields_filled_in():
    i18n.use("en")
    assert tr("Save") == "Save"
    assert tr('Exported "{name}"', name="Knight") == 'Exported "Knight"'


def test_polish_and_the_fallback_to_english():
    i18n.use("pl")
    assert tr("Save") == "Zapisz"
    assert tr('Exported "{name}"', name="Knight") == "Wyeksportowano „Knight”"
    assert tr("Not in any catalog") == "Not in any catalog"


def test_unknown_language_falls_back_to_english():
    i18n.use("xx")
    assert i18n.current() == "en"


def test_plurals():
    i18n.use("en")
    assert [tr_n(n, "{n} region", "{n} regions") for n in (1, 2)] == ["1 region", "2 regions"]
    i18n.use("pl")
    got = [tr_n(n, "{n} region", "{n} regions") for n in (1, 2, 4, 5, 12, 22, 25, 0)]
    assert got == [
        "1 region",
        "2 regiony",
        "4 regiony",
        "5 regionów",
        "12 regionów",
        "22 regiony",
        "25 regionów",
        "0 regionów",
    ]


def fields(text):
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


def test_translations_keep_the_same_fields():
    for english, polish in POLISH.items():
        assert fields(polish) == fields(english), english
    for english, forms in POLISH_PLURALS.items():
        for form in forms:
            assert fields(form) == fields(english), english


def texts_passed_to_tr():
    """Every literal text the code passes to tr() or tr_n()."""
    for path in SOURCE.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) in ("tr", "tr_n"):
                index = 0 if node.func.id == "tr" else 1
                arg = node.args[index] if len(node.args) > index else None
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    yield node.func.id, arg.value, f"{path.name}:{node.lineno}"


def test_every_text_in_the_code_has_a_polish_translation():
    found = list(texts_passed_to_tr())
    assert len(found) > 50  # the scan really finds the app's texts
    missing = [
        where
        for kind, text, where in found
        if (text not in POLISH if kind == "tr" else text not in POLISH_PLURALS)
    ]
    assert missing == []


def test_sound_names_are_translated():
    from tibia_mirror.ui.controls.dialogs import SOUND_LABELS

    assert all(label in POLISH for label in SOUND_LABELS.values())
