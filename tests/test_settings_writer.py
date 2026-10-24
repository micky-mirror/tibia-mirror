"""The writer of the settings file: when it writes."""

from tibia_mirror.app_parts.settings_writer import SettingsWriter
from tibia_mirror.settings.app_settings_store import AppSettingsStore


class FakeWindow:
    """Stands in for the app window. It remembers the functions that wait to be run."""

    def __init__(self) -> None:
        self.planned = {}  # job -> the function given to after()
        self._job_count = 0

    def after(self, delay_ms, function):
        self._job_count += 1
        job = f"job{self._job_count}"
        self.planned[job] = function
        return job

    def after_cancel(self, job):
        del self.planned[job]

    def run_planned(self) -> None:
        """Run every waiting function, as the real window does when the wait is over."""
        functions = list(self.planned.values())
        self.planned.clear()

        for function in functions:
            function()


def do_nothing(previous, current):
    pass


def test_nothing_is_written_before_the_wait_is_over(tmp_path):
    file = tmp_path / "settings.json"
    window = FakeWindow()
    writer = SettingsWriter(window, AppSettingsStore(file, do_nothing), lambda: None)

    writer.write_on_delay()

    assert not file.exists()


def test_the_settings_are_written_when_the_wait_is_over(tmp_path):
    file = tmp_path / "settings.json"
    window = FakeWindow()
    settings = AppSettingsStore(file, do_nothing)
    writer = SettingsWriter(window, settings, lambda: None)
    settings.update(theme="light")

    writer.write_on_delay()
    window.run_planned()

    assert AppSettingsStore(file, do_nothing).current.theme == "light"


def test_many_quick_changes_give_one_write(tmp_path):
    file = tmp_path / "settings.json"
    window = FakeWindow()
    writer = SettingsWriter(window, AppSettingsStore(file, do_nothing), lambda: None)

    writer.write_on_delay()
    writer.write_on_delay()
    writer.write_on_delay()

    assert len(window.planned) == 1


def test_a_new_write_can_be_planned_after_a_write(tmp_path):
    file = tmp_path / "settings.json"
    window = FakeWindow()
    writer = SettingsWriter(window, AppSettingsStore(file, do_nothing), lambda: None)
    writer.write_on_delay()
    window.run_planned()
    file.unlink()

    writer.write_on_delay()
    window.run_planned()

    assert file.exists()
