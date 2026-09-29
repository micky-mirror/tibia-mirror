"""One copy of the app at a time: two would show every mirror twice and overwrite
each other's settings.

The first copy holds a named mutex. A later copy signals a named event and quits;
the first one sees it on its next poll and brings its panel to the front.
"""

from tibia_mirror import win32


class SingleInstance:
    def __init__(self, name: str) -> None:
        self._mutex, existed = win32.create_mutex(f"Local\\{name}")
        self.first = not existed
        self._show = win32.create_event(f"Local\\{name}.show")

    def ask_first_to_show(self) -> None:
        """For a later copy: bring the first copy's panel to the front.

        This copy was just started, so it is in front and may hand that on.
        """
        win32.allow_any_to_take_foreground()
        win32.set_event(self._show)

    def show_requested(self) -> bool:
        """For the first copy: whether a later copy asked for the panel since the last check."""
        return win32.take_event(self._show)
