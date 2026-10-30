"""The error log. The .exe has no console, so errors are written to a file."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType

_logger = logging.getLogger("tibia_mirror")


def start(path: Path, max_bytes: int) -> None:
    """Write every error that nothing catches to this file, from now on."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # at max_bytes the file becomes error.log.1, and a new error.log starts
    handler = RotatingFileHandler(
        path, maxBytes=max_bytes, backupCount=1, encoding="utf-8", delay=True
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
    _logger.addHandler(handler)
    sys.excepthook = log_exception


def log_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    """Write this error to the log."""
    _logger.error("Error", exc_info=(exc_type, exc_value, exc_traceback))
