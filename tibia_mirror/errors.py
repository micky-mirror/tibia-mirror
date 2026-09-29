"""The error log, since the .exe has no console: uncaught exceptions, Tk callback
errors and hard crashes. Only errors are written, never what the user does.
Once too big, it is trimmed on the next start.
"""

import faulthandler
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path
from types import TracebackType
from typing import TextIO

_log: TextIO | None = None
_max_bytes = 0
_full = False


def start(path: Path, max_bytes: int) -> None:
    global _log, _max_bytes, _full
    path.parent.mkdir(parents=True, exist_ok=True)
    trim(path, max_bytes)
    # Line-buffered, so each line is on disk even if the process dies right after.
    _log = path.open("a", encoding="utf-8", buffering=1)
    _max_bytes, _full = max_bytes, False
    faulthandler.enable(_log)
    sys.excepthook = log_exception
    threading.excepthook = lambda args: log_exception(
        args.exc_type, args.exc_value, args.exc_traceback
    )


def trim(path: Path, max_bytes: int) -> None:
    """Keep only the newest half of the log, from a line start, once it has reached max_bytes."""
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return
    if len(data) < max_bytes:
        return
    tail = data[-(max_bytes // 2) :]
    path.write_bytes(tail[tail.find(b"\n") + 1 :])


def log_exception(
    exc_type: type[BaseException],
    value: BaseException | None,
    tb: TracebackType | None,
) -> None:
    """Write the error to the log, and to the console when there is one."""
    global _full
    text = "".join(traceback.format_exception(exc_type, value, tb))
    if sys.stderr is not None:
        sys.stderr.write(text)
    if _log is None or _full:
        return
    if _log.tell() >= _max_bytes:
        _full = True
        _log.write("Log full: further errors are dropped until the next start.\n")
        return
    _log.write(f"--- {datetime.now():%Y-%m-%d %H:%M:%S}\n{text}")
