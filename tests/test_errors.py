import faulthandler
import sys
import threading

import pytest

from tibia_mirror import errors


@pytest.fixture
def log(tmp_path):
    """Start the error log in a temp folder, and undo everything start() changed."""
    path = tmp_path / "data" / "error.log"

    def start(max_bytes=10_000):
        errors.start(path, max_bytes)
        return path

    yield start
    faulthandler.disable()
    sys.excepthook = sys.__excepthook__
    threading.excepthook = threading.__excepthook__
    if errors._log is not None:
        errors._log.close()
        errors._log = None


def raised(message):
    try:
        raise ValueError(message)
    except ValueError as e:
        return type(e), e, e.__traceback__


def test_writes_the_time_and_traceback(log):
    path = log()
    errors.log_exception(*raised("boom"))
    text = path.read_text(encoding="utf-8")
    assert text.startswith("--- ")
    assert "Traceback (most recent call last)" in text
    assert "ValueError: boom" in text


def test_uncaught_exceptions_go_to_the_log(log):
    path = log()
    sys.excepthook(*raised("uncaught"))
    assert "ValueError: uncaught" in path.read_text(encoding="utf-8")


def test_errors_past_the_limit_are_dropped_with_one_note(log):
    path = log(max_bytes=2_000)
    for n in range(50):
        errors.log_exception(*raised(f"error {n}"))
    text = path.read_text(encoding="utf-8")
    assert "error 0" in text
    assert "error 49" not in text
    assert text.count("Log full") == 1
    assert len(text.encode()) < 4_000


def test_trim_keeps_the_newest_half_from_a_line_start(tmp_path):
    path = tmp_path / "error.log"
    path.write_bytes(b"".join(b"line %03d\n" % n for n in range(200)))  # 1800 bytes
    errors.trim(path, 1_000)
    data = path.read_bytes()
    assert len(data) <= 500
    assert data.startswith(b"line ")
    assert data.endswith(b"line 199\n")


def test_trim_leaves_a_small_log_alone(tmp_path):
    path = tmp_path / "error.log"
    path.write_bytes(b"line\n")
    errors.trim(path, 1_000)
    assert path.read_bytes() == b"line\n"
    errors.trim(tmp_path / "missing.log", 1_000)  # no log yet: nothing to do
