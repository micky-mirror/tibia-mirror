from tibia_mirror.services.mirrors import Mirrors


class FakeMirror:
    """Stands in for a mirror window: it only records how it was closed."""

    def __init__(self):
        self.closed = None

    def fade_out_and_destroy(self):
        self.closed = "faded"

    def destroy(self):
        self.closed = "at once"


def test_starts_empty():
    mirrors = Mirrors()
    assert len(mirrors) == 0
    assert not mirrors
    assert list(mirrors) == []


def test_keeps_the_order_mirrors_were_added():
    first, second = FakeMirror(), FakeMirror()
    mirrors = Mirrors()
    mirrors.append(first)
    mirrors.append(second)
    assert list(mirrors) == [first, second]
    assert len(mirrors) == 2


def test_knows_which_mirrors_it_holds():
    first, second = FakeMirror(), FakeMirror()
    mirrors = Mirrors()
    mirrors.append(first)
    assert first in mirrors
    assert second not in mirrors


def test_remove_takes_out_only_that_mirror_and_fades_it():
    first, second = FakeMirror(), FakeMirror()
    mirrors = Mirrors()
    mirrors.append(first)
    mirrors.append(second)
    mirrors.remove(first)
    assert list(mirrors) == [second]
    assert first.closed == "faded"
    assert second.closed is None


def test_remove_still_closes_a_mirror_it_does_not_hold():
    stray = FakeMirror()
    Mirrors().remove(stray)
    assert stray.closed == "faded"


def test_clear_closes_every_mirror_at_once():
    first, second = FakeMirror(), FakeMirror()
    mirrors = Mirrors()
    mirrors.append(first)
    mirrors.append(second)
    mirrors.clear()
    assert not mirrors
    assert first.closed == second.closed == "at once"
