import pytest

from tibia_mirror.services import mirrors as mirrors_module
from tibia_mirror.services.mirrors import Mirrors

ROOT, GAME, CLIENT, LOOK = "root", 100, "client", "look"


def on_remove(mirror):
    pass


def on_changed(mirror):
    pass


class FakeMirror:
    """Stands in for a mirror window: it records how it was made and how it was closed."""

    def __init__(self, root, game_hwnd, saved, client, look, on_remove, on_changed):
        if saved == "refused":
            raise OSError("DWM refused")
        self.made_with = (root, game_hwnd, saved, client, look, on_remove, on_changed)
        self.closed = None

    def fade_out_and_destroy(self):
        self.closed = "faded"

    def destroy(self):
        self.closed = "at once"

    def attach(self, game_hwnd, client):
        if self.made_with[2] == "stubborn":
            raise OSError("DWM refused")
        self.attached = (game_hwnd, client)

    def detach(self):
        self.attached = None

    def set_client(self, client):
        self.client = client

    def set_look(self, look):
        self.look = look

    def set_visible(self, show):
        self.visible = show


@pytest.fixture
def mirrors(monkeypatch):
    monkeypatch.setattr(mirrors_module, "MirrorWindow", FakeMirror)
    return Mirrors(ROOT, on_remove, on_changed)


def test_starts_empty(mirrors):
    assert len(mirrors) == 0
    assert not mirrors
    assert list(mirrors) == []


def test_keeps_the_order_mirrors_were_added(mirrors):
    first = mirrors.add("first", GAME, CLIENT, LOOK)
    second = mirrors.add("second", GAME, CLIENT, LOOK)
    assert list(mirrors) == [first, second]
    assert len(mirrors) == 2


def test_add_hands_the_window_what_it_needs(mirrors):
    mirror = mirrors.add("saved", GAME, CLIENT, LOOK)
    assert mirror.made_with == (ROOT, GAME, "saved", CLIENT, LOOK, on_remove, on_changed)


def test_add_gives_nothing_when_windows_refuses(mirrors):
    assert mirrors.add("refused", GAME, CLIENT, LOOK) is None
    assert not mirrors


def test_knows_which_mirrors_it_holds(mirrors):
    held = mirrors.add("held", GAME, CLIENT, LOOK)
    stray = FakeMirror(ROOT, GAME, "stray", CLIENT, LOOK, on_remove, on_changed)
    assert held in mirrors
    assert stray not in mirrors


def test_remove_takes_out_only_that_mirror_and_fades_it(mirrors):
    first = mirrors.add("first", GAME, CLIENT, LOOK)
    second = mirrors.add("second", GAME, CLIENT, LOOK)
    mirrors.remove(first)
    assert list(mirrors) == [second]
    assert first.closed == "faded"
    assert second.closed is None


def test_remove_still_closes_a_mirror_it_does_not_hold(mirrors):
    stray = FakeMirror(ROOT, GAME, "stray", CLIENT, LOOK, on_remove, on_changed)
    mirrors.remove(stray)
    assert stray.closed == "faded"


def test_clear_closes_every_mirror_at_once(mirrors):
    first = mirrors.add("first", GAME, CLIENT, LOOK)
    second = mirrors.add("second", GAME, CLIENT, LOOK)
    mirrors.clear()
    assert not mirrors
    assert first.closed == second.closed == "at once"


def test_attach_points_every_mirror_at_the_new_game_window(mirrors):
    first = mirrors.add("first", GAME, CLIENT, LOOK)
    second = mirrors.add("second", GAME, CLIENT, LOOK)
    assert mirrors.attach(200, "new client") == 0
    assert first.attached == second.attached == (200, "new client")


def test_attach_counts_the_mirrors_windows_refused(mirrors):
    mirrors.add("stubborn", GAME, CLIENT, LOOK)
    fine = mirrors.add("fine", GAME, CLIENT, LOOK)
    assert mirrors.attach(200, "new client") == 1
    assert fine.attached == (200, "new client")


def test_detach_and_set_client_reach_every_mirror(mirrors):
    first = mirrors.add("first", GAME, CLIENT, LOOK)
    second = mirrors.add("second", GAME, CLIENT, LOOK)
    mirrors.set_client("moved")
    assert first.client == second.client == "moved"
    mirrors.attach(200, "new client")
    mirrors.detach()
    assert first.attached is None
    assert second.attached is None


def test_set_look_and_set_visible_reach_every_mirror(mirrors):
    first = mirrors.add("first", GAME, CLIENT, LOOK)
    second = mirrors.add("second", GAME, CLIENT, LOOK)
    mirrors.set_look("new look")
    assert first.look == second.look == "new look"
    mirrors.set_visible(True)
    assert first.visible
    assert second.visible
