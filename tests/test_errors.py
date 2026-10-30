"""The error log: each error is written to a file, with its time and traceback."""

import re
import sys

import pytest

from tibia_mirror import errors


@pytest.fixture
def log_file(tmp_path):
    """The error log in a new folder. What start() changed is undone after the test."""
    yield tmp_path / "data" / "error.log"
    for handler in list(errors._logger.handlers):
        handler.close()
        errors._logger.removeHandler(handler)
    sys.excepthook = sys.__excepthook__


def raised(message):
    """An error as Python reports it: its type, the error itself and its traceback."""
    try:
        raise ValueError(message)
    except ValueError as error:
        return type(error), error, error.__traceback__


def test_no_file_is_made_before_the_first_error(log_file):
    errors.start(log_file, 10_000)

    assert not log_file.exists()


def test_an_error_is_written_with_its_time_and_traceback(log_file):
    errors.start(log_file, 10_000)

    errors.log_exception(*raised("boom"))

    text = log_file.read_text(encoding="utf-8")
    assert re.match(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d Error\n", text)
    assert "Traceback (most recent call last)" in text
    assert "ValueError: boom" in text


def test_an_error_that_nothing_catches_is_written(log_file):
    errors.start(log_file, 10_000)

    sys.excepthook(*raised("uncaught"))

    assert "ValueError: uncaught" in log_file.read_text(encoding="utf-8")


def test_a_full_log_moves_to_a_second_file_at_start(log_file):
    log_file.parent.mkdir()
    log_file.write_text("old error\n" * 300, encoding="utf-8")

    errors.start(log_file, 2_000)
    errors.log_exception(*raised("new error"))

    assert "old error" in log_file.with_name("error.log.1").read_text(encoding="utf-8")
    assert "old error" not in log_file.read_text(encoding="utf-8")
    assert "new error" in log_file.read_text(encoding="utf-8")
