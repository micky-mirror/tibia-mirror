"""The error log. The .exe has no console, so errors are written to a file."""

import logging
import sys
from pathlib import Path
from types import TracebackType

_logger = logging.getLogger("tibia_mirror")


def start(path: Path, max_bytes: int) -> None:
    """Write every error that nothing catches to this file, from now on."""
    path.parent.mkdir(parents=True, exist_ok=True)
    _move_full_log(path, max_bytes)
    handler = logging.FileHandler(path, encoding="utf-8", delay=True)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    _logger.addHandler(handler)
    sys.excepthook = log_exception


def _move_full_log(path: Path, max_bytes: int) -> None:
    """Move a log over `max_bytes` to error.log.1, so a new one starts."""
    if path.exists() and path.stat().st_size > max_bytes:
        path.replace(path.with_name(path.name + ".1"))


def log_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    """Write this error to the log."""
    _logger.error("Error", exc_info=(exc_type, exc_value, exc_traceback))
