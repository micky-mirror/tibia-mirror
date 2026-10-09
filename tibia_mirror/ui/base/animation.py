"""Time-based tweens on the Tk event loop."""

import time
import tkinter as tk
from collections.abc import Callable

FRAME_MS = 15


def ease_out_cubic(progress: float) -> float:
    """Fast at first, slowing to a stop: 0..1 in, 0..1 out."""
    return 1 - (1 - progress) ** 3


def lerp(start: float, end: float, progress: float) -> float:
    """The value `progress` (0..1) of the way from start to end ("linear interpolation")."""
    return start + (end - start) * progress


class Tween:
    """Calls on_step(value) from `start` to `end` over `duration_ms`, then on_done().

    Timed by the clock, so a busy event loop drops frames instead of slowing down.
    """

    def __init__(
        self,
        widget: tk.Misc,
        start: float,
        end: float,
        duration_ms: int,
        on_step: Callable[[float], None],
        on_done: Callable[[], None] | None = None,
    ) -> None:
        self._widget = widget
        self._start, self._end = start, end
        self._duration = max(0, duration_ms) / 1000
        self._on_step, self._on_done = on_step, on_done
        self._began = time.perf_counter()
        self._frame_job: str | None = None
        self._tick()

    def _tick(self) -> None:
        elapsed = time.perf_counter() - self._began
        progress = 1.0 if self._duration == 0 else min(1.0, elapsed / self._duration)
        self._on_step(lerp(self._start, self._end, ease_out_cubic(progress)))
        if progress < 1.0:
            self._frame_job = self._widget.after(FRAME_MS, self._tick)
            return
        self._frame_job = None
        if self._on_done:
            self._on_done()

    def cancel(self) -> None:
        if self._frame_job is not None:
            self._widget.after_cancel(self._frame_job)
            self._frame_job = None
