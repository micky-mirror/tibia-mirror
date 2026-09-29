import time

from tibia_mirror import win32
from tibia_mirror.rawinput import InputWatcher

SHIFT, CTRL, A = 0xA0, 0x11, 0x41


def make_watcher():
    calls = []
    watcher = InputWatcher(
        on_click=lambda *args: calls.append(("click", *args)),
        on_key=lambda *args: calls.append(("key", *args)),
    )
    return watcher, calls


def test_click_waits_for_dispatch():
    # The window procedure runs inside Tk's event loop, where the callbacks must not run.
    watcher, calls = make_watcher()
    watcher._note_click("left")
    assert calls == []
    watcher.dispatch()
    assert [c[:2] for c in calls] == [("click", "left")]


def test_click_keeps_cursor_and_time_of_the_press(monkeypatch):
    watcher, calls = make_watcher()
    monkeypatch.setattr(win32, "cursor_pos", lambda: (120, 340))
    before = time.monotonic()
    watcher._note_click("right")
    monkeypatch.setattr(win32, "cursor_pos", lambda: (999, 999))  # moved before the dispatch
    watcher.dispatch()
    ((_, button, x, y, at),) = calls
    assert (button, x, y) == ("right", 120, 340)
    assert before <= at <= time.monotonic()


def test_key_waits_for_dispatch_with_held_modifiers():
    watcher, calls = make_watcher()
    watcher._note_key(CTRL, down=True)
    watcher._note_key(A, down=True)
    assert calls == []
    watcher.dispatch()
    assert calls == [("key", A, ("ctrl",))]


def test_key_repeat_and_modifiers_alone_are_ignored():
    watcher, calls = make_watcher()
    watcher._note_key(SHIFT, down=True)
    watcher._note_key(A, down=True)
    watcher._note_key(A, down=True)  # auto-repeat
    watcher._note_key(A, down=False)
    watcher._note_key(SHIFT, down=False)
    watcher._note_key(A, down=True)
    watcher.dispatch()
    assert calls == [("key", A, ("shift",)), ("key", A, ())]


def test_dispatch_keeps_order_and_empties_the_queue():
    watcher, calls = make_watcher()
    watcher._note_key(A, down=True)
    watcher._note_click("left")
    watcher.dispatch()
    watcher.dispatch()
    assert [c[:2] for c in calls] == [("key", A), ("click", "left")]
