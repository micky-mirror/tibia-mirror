from tibia_mirror.services.mirrors import Mirrors

# Stand-ins: the list never looks inside a mirror, so no window is needed.
FIRST, SECOND = object(), object()


def test_starts_empty():
    mirrors = Mirrors()
    assert len(mirrors) == 0
    assert not mirrors
    assert list(mirrors) == []


def test_keeps_the_order_mirrors_were_added():
    mirrors = Mirrors()
    mirrors.append(FIRST)
    mirrors.append(SECOND)
    assert list(mirrors) == [FIRST, SECOND]
    assert len(mirrors) == 2


def test_knows_which_mirrors_it_holds():
    mirrors = Mirrors()
    mirrors.append(FIRST)
    assert FIRST in mirrors
    assert SECOND not in mirrors


def test_remove_takes_out_only_that_mirror():
    mirrors = Mirrors()
    mirrors.append(FIRST)
    mirrors.append(SECOND)
    mirrors.remove(FIRST)
    assert list(mirrors) == [SECOND]


def test_clear_empties_it():
    mirrors = Mirrors()
    mirrors.append(FIRST)
    mirrors.clear()
    assert not mirrors
