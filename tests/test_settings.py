import json

from tibia_mirror import settings
from tibia_mirror.config import MIN_OPACITY
from tibia_mirror.settings import Settings


def test_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    changed = Settings(
        autosave=True,
        new_opacity=0.8,
        mirror_frame=False,
        fades=False,
        panel_on_top=True,
        profile="Knight",
        theme="light",
        hide_all_key=72,
        hide_all_modifiers=("ctrl", "shift"),
        profile_per_character=True,
        characters=(("Knight Name", "EK"), ("Sorcerer", "MS")),
        timer_pauses=(("Knight Name", "abc", 12.5), ("Sorcerer", "def", 300.0)),
        last_character="Knight Name",
        panel_rect=(-8, 120, 625, 1180),
    )
    settings.save(path, changed)
    assert settings.load(path) == changed


def test_missing_or_broken_file_gives_defaults(tmp_path):
    assert settings.load(tmp_path / "missing.json") == Settings()
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    assert settings.load(broken) == Settings()
    listed = tmp_path / "list.json"
    listed.write_text("[1, 2]")
    assert settings.load(listed) == Settings()


def test_wrong_types_fall_back_per_field(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "autosave": 1,  # not a bool
                "fades": False,
                "new_opacity": True,  # bool is not a number
                "profile": "",
                "unknown": "ignored",
            }
        )
    )
    loaded = settings.load(path)
    assert loaded.autosave is False
    assert loaded.fades is False
    assert loaded.new_opacity == Settings().new_opacity
    assert loaded.profile == Settings().profile


def test_numbers_are_clamped(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"new_opacity": 0, "max_mirror_side": 600}))  # old key: ignored
    loaded = settings.load(path)
    assert loaded.new_opacity == MIN_OPACITY


def test_unknown_theme_falls_back_to_dark(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "neon"}))
    assert settings.load(path).theme == "dark"


def test_language_is_kept_and_unknown_ones_fall_back_to_english(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"language": "pl"}))
    assert settings.load(path).language == "pl"
    path.write_text(json.dumps({"language": "de"}))
    assert settings.load(path).language == "en"


def test_hide_all_key_is_not_set_by_default():
    assert Settings().hide_all_combo is None


def test_hide_all_combo():
    assert Settings(hide_all_key=72, hide_all_modifiers=("ctrl",)).hide_all_combo == (
        72,
        ("ctrl",),
    )


def test_bad_hide_all_key_is_dropped_and_modifiers_are_cleaned(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"hide_all_key": 72.5, "hide_all_modifiers": ["shift", "win"]}))
    loaded = settings.load(path)
    assert loaded.hide_all_key is None
    assert loaded.hide_all_modifiers == ("shift",)
    path.write_text(json.dumps({"hide_all_key": 300, "hide_all_modifiers": "ctrl"}))
    loaded = settings.load(path)
    assert loaded.hide_all_key is None
    assert loaded.hide_all_modifiers == ()


def test_panel_opens_centred_until_it_has_a_place(tmp_path):
    assert Settings().panel_rect is None
    path = tmp_path / "settings.json"
    for bad in ([10, 20, 500], [10, 20, 0, 900], [10, 20, 500.5, 900], [True, 20, 500, 900], "x"):
        path.write_text(json.dumps({"panel_rect": bad}))
        assert settings.load(path).panel_rect is None, bad
