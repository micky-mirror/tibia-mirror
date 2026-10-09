import pytest

from tibia_mirror.core.settings import Settings
from tibia_mirror.services.settings_store import SettingsStore


@pytest.fixture
def path(tmp_path):
    return tmp_path / "settings.json"


def nothing():
    pass


def test_starts_with_the_defaults_when_there_is_no_file(path):
    assert SettingsStore(path, nothing).current == Settings()


def test_update_changes_the_settings_and_tells_the_app(path):
    calls = []
    store = SettingsStore(path, lambda: calls.append("changed"))
    store.update(theme="light", autosave=True)
    assert store.current.theme == "light"
    assert store.current.autosave
    assert calls == ["changed"]


def test_update_does_not_write_the_file(path):
    SettingsStore(path, nothing).update(autosave=True)
    assert not path.exists()


def test_update_with_a_wrong_name_raises(path):
    with pytest.raises(TypeError):
        SettingsStore(path, nothing).update(no_such_setting=1)


def test_save_writes_the_file_and_a_new_store_reads_it(path):
    store = SettingsStore(path, nothing)
    store.update(autosave=True)
    store.save()
    assert SettingsStore(path, nothing).current.autosave
