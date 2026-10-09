import uuid

from tibia_mirror.winapi.instance import SingleInstance


def unique_name():
    # Named objects are shared by the whole Windows session: never reuse the app's.
    return f"TibiaMirrorTest.{uuid.uuid4().hex}"


def test_only_the_first_copy_is_first():
    name = unique_name()
    first = SingleInstance(name)
    later = SingleInstance(name)
    assert first.first
    assert not later.first


def test_a_later_copy_asks_the_first_to_show_once():
    name = unique_name()
    first = SingleInstance(name)
    assert not first.show_requested()
    SingleInstance(name).ask_first_to_show()
    assert first.show_requested()
    assert not first.show_requested()  # taken by the check above
