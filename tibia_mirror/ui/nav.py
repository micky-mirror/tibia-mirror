"""The navigation rail down the left edge of the control panel."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from tibia_mirror.i18n import tr
from tibia_mirror.ui import theme
from tibia_mirror.ui.images import photo
from tibia_mirror.ui.render import ButtonStyle, button_pixels
from tibia_mirror.ui.scale import px


@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    glyph: str  # FONT_ICON code point
    pinned_bottom: bool = False  # stacked up from the rail's bottom edge, like Settings


class NavRail(tk.Canvas):
    """The menu down the panel's left edge: an icon over a label per section.

    Drawn on one canvas like RegionCard; pinned entries stack up from the bottom.
    A click selects an entry and calls on_select(key).
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    WIDTH = 100  # room around "Ustawienia", the longest label
    TOP_PAD = 16  # above the first item
    BOTTOM_PAD = 10  # below the last one
    ITEM_HEIGHT = 68
    PILL_WIDTH = 48
    PILL_HEIGHT = 30
    LABEL_GAP = 4

    def __init__(
        self,
        parent: tk.Misc,
        items: Sequence[NavItem],
        selected: str,
        on_select: Callable[[str], None],
    ) -> None:
        super().__init__(parent, width=px(self.WIDTH), bg=theme.MANTLE, highlightthickness=0, bd=0)
        self._items = items
        self._selected = selected
        self._hovered: str | None = None
        self._pressed: str | None = None
        self._on_select = on_select

        pill_height = px(self.PILL_HEIGHT)
        self._pills = {
            fill: photo(
                self,
                button_pixels(
                    px(self.PILL_WIDTH),
                    pill_height,
                    ButtonStyle(fill=fill, radius=pill_height // 2),
                    theme.MANTLE,
                ),
            )
            for fill in (theme.SURFACE, theme.ACCENT_TINT)
        }
        center_x = px(self.WIDTH) // 2
        self._drawn: list[tuple[int, int, int]] = []  # (pill, glyph, label) items per entry
        for item in items:
            self._drawn.append(
                (
                    self.create_image(center_x, 0, state="hidden"),
                    self.create_text(center_x, 0, text=item.glyph, font=theme.FONT_ICON_LARGE),
                    self.create_text(
                        center_x, 0, text=tr(item.label), anchor="n", font=theme.FONT_CAPTION
                    ),
                )
            )
        self._tops = [0] * len(items)
        self._layout(0)
        self._draw()
        self.bind("<Configure>", lambda e: self._layout(e.height))

        # <Enter> too: the pointer may land on an entry and rest there with no <Motion>.
        for sequence in ("<Enter>", "<Motion>"):
            self.bind(sequence, lambda e: self._set_hovered(self._key_at(e)))
        self.bind("<Leave>", lambda e: self._set_hovered(None))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)

    def _layout(self, height: int) -> None:
        top = [i for i in self._items if not i.pinned_bottom]
        bottom = [i for i in self._items if i.pinned_bottom]
        center_x = px(self.WIDTH) // 2
        item_height, half_pill = px(self.ITEM_HEIGHT), px(self.PILL_HEIGHT) // 2
        for n, item in enumerate(self._items):
            if item.pinned_bottom:
                below = len(bottom) - bottom.index(item)
                y = height - px(self.BOTTOM_PAD) - below * item_height
            else:
                y = px(self.TOP_PAD) + top.index(item) * item_height
            self._tops[n] = y
            pill_y = y + half_pill
            pill, glyph, label = self._drawn[n]
            self.coords(pill, center_x, pill_y)
            self.coords(glyph, center_x, pill_y)
            self.coords(label, center_x, pill_y + half_pill + px(self.LABEL_GAP))

    def _key_at(self, e: tk.Event[tk.Canvas]) -> str | None:
        if not 0 <= e.x < px(self.WIDTH):
            return None
        for item, top in zip(self._items, self._tops, strict=True):
            if top <= e.y < top + px(self.ITEM_HEIGHT):
                return item.key
        return None

    def _draw(self) -> None:
        for item, (pill, glyph, label) in zip(self._items, self._drawn, strict=True):
            if item.key == self._selected:
                image, glyph_fill, label_fill = (
                    self._pills[theme.ACCENT_TINT],
                    theme.ACCENT,
                    theme.TEXT,
                )
            elif item.key == self._hovered:
                image, glyph_fill, label_fill = self._pills[theme.SURFACE], theme.TEXT, theme.TEXT
            else:
                image, glyph_fill, label_fill = None, theme.SUBTEXT, theme.SUBTEXT
            self.itemconfigure(pill, image=image or "", state="normal" if image else "hidden")
            self.itemconfigure(glyph, fill=glyph_fill)
            self.itemconfigure(label, fill=label_fill)
        clickable = self._hovered not in (None, self._selected)
        self.configure(cursor="hand2" if clickable else "")

    def _set_hovered(self, key: str | None) -> None:
        if key != self._hovered:
            self._hovered = key
            self._draw()

    def _press(self, e: tk.Event[tk.Canvas]) -> None:
        self._pressed = self._key_at(e)

    def _release(self, e: tk.Event[tk.Canvas]) -> None:
        key, self._pressed = self._pressed, None
        if key is not None and key == self._key_at(e) and key != self._selected:
            self._selected = key
            self._draw()
            self._on_select(key)
