"""Key combinations: a key and the modifier keys held with it."""

from typing import TypeGuard

# Modifier keys a key can be combined with, in the order they are written.
MODIFIERS = ("ctrl", "shift", "alt")
MODIFIER_NAMES = {"ctrl": "Ctrl", "shift": "Shift", "alt": "Alt"}

# A key combination: a Windows virtual-key code and the modifiers held with it,
# from MODIFIERS in their order, e.g. (120, ("shift",)) for Shift+F9.
KeyCombo = tuple[int, tuple[str, ...]]


def _is_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def parse_key(value: object) -> int | None:
    """A Windows virtual-key code read from a file, or None if `value` is not one."""
    return value if _is_int(value) and 0 < value < 256 else None


def canonical_modifiers(names: object) -> tuple[str, ...]:
    """Known modifier names, each once, in MODIFIERS order (anything else is dropped)."""
    names = names if isinstance(names, list | tuple | set | frozenset) else ()
    return tuple(modifier for modifier in MODIFIERS if modifier in names)


def combo_name(modifiers: tuple[str, ...], key_name: str) -> str:
    """How a key combination is written, e.g. "Ctrl+Shift+F9"."""
    names = [MODIFIER_NAMES[modifier] for modifier in canonical_modifiers(modifiers)]
    return "+".join([*names, key_name])


def combo_matches(combo: KeyCombo | None, vk: int, modifiers: tuple[str, ...]) -> bool:
    """Whether pressing `vk` with exactly `modifiers` held is `combo` (None matches nothing)."""
    return combo is not None and combo == (vk, canonical_modifiers(modifiers))
