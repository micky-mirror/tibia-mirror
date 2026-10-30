"""Reading a profile from its file, and writing it back."""

import json

import pytest

from tibia_mirror.core.mirrors.mirror_settings import MirrorSettings
from tibia_mirror.core.profile import Profile

# One mirror as a profile file holds it, and the same mirror as the class holds it.
MIRROR_JSON = {
    "id": "mirror-1",
    "name": "Minimap",
    "layouts": {"1920x1080": {"region": [10, 20, 300, 40], "offset": [5, 6]}},
}
MIRROR = MirrorSettings.from_json(MIRROR_JSON)


def test_the_mirrors_are_read() -> None:
    profile = Profile.from_json({"version": 2, "mirrors": [MIRROR_JSON]})

    assert profile == Profile(mirrors=(MIRROR,))


def test_a_file_that_is_only_a_list_of_mirrors_is_read() -> None:
    profile = Profile.from_json([MIRROR_JSON])

    assert profile == Profile(mirrors=(MIRROR,))


def test_the_file_gets_the_version_number() -> None:
    assert Profile().to_json() == {"version": 2, "mirrors": []}


def test_a_written_profile_is_read_back_the_same() -> None:
    profile = Profile(mirrors=(MIRROR,))
    file_content = json.loads(json.dumps(profile.to_json()))

    assert Profile.from_json(file_content) == profile


def test_content_that_is_not_an_object_or_a_list_is_refused() -> None:
    with pytest.raises(ValueError, match="the profile file is invalid"):
        Profile.from_json("Minimap")


def test_a_file_without_mirrors_is_refused() -> None:
    with pytest.raises(ValueError, match="the profile file is invalid"):
        Profile.from_json({"version": 2})


def test_mirrors_that_are_not_a_list_are_refused() -> None:
    with pytest.raises(ValueError, match="the profile file is invalid"):
        Profile.from_json({"version": 2, "mirrors": {"name": "Minimap"}})


def test_a_layout_without_its_region_is_refused() -> None:
    broken_mirror = MIRROR_JSON | {"layouts": {"1920x1080": {"offset": [5, 6]}}}

    with pytest.raises(ValueError, match="the profile file is invalid"):
        Profile.from_json({"version": 2, "mirrors": [broken_mirror]})
