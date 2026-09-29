"""Dropdowns: the profile picker and its menu, the colour picker, and option fields."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial

from tibia_mirror import dwm, win32
from tibia_mirror.geometry import Box
from tibia_mirror.ui import theme
from tibia_mirror.ui.images import photo
from tibia_mirror.ui.render import ButtonStyle, button_pixels, outlined_pixels
from tibia_mirror.ui.scale import px
from tibia_mirror.ui.text import elide

# Segoe MDL2 Assets code points (FONT_ICON).
GLYPH_CHECK = "\ue73e"
GLYPH_PROFILE = "\ue77b"
GLYPH_CHEVRON_DOWN = "\ue70d"
GLYPH_CHEVRON_UP = "\ue70e"


@dataclass(frozen=True)
class MenuItem:
    label: str
    command: Callable[[], None]
    checked: bool = False
    enabled: bool = True
    danger: bool = False


SEPARATOR = None  # in a PopupMenu item list

# A menu row: its top and bottom on the menu's canvas, and its item.
_Row = tuple[int, int, MenuItem]


class _Dropdown:
    """A borderless popup under an anchor box (screen x0, y0, x1, y1).

    Closes on Escape, a click outside, or when the app loses focus, then calls
    on_close(). Subclasses draw on `self.canvas` and call _show_under(box).
    """

    GAP = 4  # between the anchor box and the popup, at 100% display scaling
    # The popup's border, 1px on each side: Windows draws it (or the popup does, on
    # Windows 10), and it stays 1px at any scaling.
    BORDER = 2

    def __init__(
        self, root: tk.Misc, width: int, inner_height: int, on_close: Callable[[], None]
    ) -> None:
        self._on_close = on_close
        self.win = tk.Toplevel(root, bg=theme.SURFACE_HI)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        # On Windows 10 a 1px SURFACE_HI frame shows around the canvas; on 11,
        # Windows draws the border itself, with rounded corners (see _show_under).
        frame = dwm.POPUP_FRAME
        self.canvas = tk.Canvas(
            self.win,
            width=width - 2 * frame,
            height=inner_height,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(padx=frame, pady=frame)
        self._size = (width, inner_height + 2 * frame)
        self.win.bind("<ButtonPress>", self._press)
        self.win.bind("<FocusOut>", lambda e: self.close() if e.widget is self.win else None)
        self.win.bind("<Escape>", lambda e: self.close())
        self.win.protocol("WM_DELETE_WINDOW", self.close)  # e.g. Alt+F4

    def _show_under(self, box: Box) -> None:
        """Below the box, left-aligned to it (above it near the bottom of the screen)."""
        x0, y0, _x1, y1 = box
        width, height = self._size
        area = win32.work_area_at((x0, y1))
        gap = px(self.GAP)
        top = y1 + gap if y1 + gap + height <= area.bottom else y0 - gap - height
        left = min(max(x0, area.x), area.right - width)
        self.win.geometry(f"{width}x{height}+{left}+{top}")
        self.win.deiconify()
        dwm.round_popup(win32.toplevel_hwnd(self.win), theme.SURFACE_HI)
        self.win.grab_set()
        self.win.focus_force()

    def _press(self, e: tk.Event[tk.Misc]) -> None:
        # Under the grab, clicks anywhere in the app arrive here.
        x, y = e.x_root - self.win.winfo_rootx(), e.y_root - self.win.winfo_rooty()
        if not (0 <= x < self.win.winfo_width() and 0 <= y < self.win.winfo_height()):
            self.close()

    def close(self) -> None:
        if not self.win.winfo_exists():
            return
        self.win.grab_release()
        self.win.destroy()
        self._on_close()


class PopupMenu(_Dropdown):
    """A list of MenuItems under `box`, as wide as it; commands run after it closes."""

    # Sizes at 100% display scaling, scaled with px() where used.
    ROW_HEIGHT = 32
    SEPARATOR_HEIGHT = 9
    PAD = 4
    CHIP_RADIUS = 6
    CHECK_X = 16  # the check mark's centre, after PAD
    TEXT_X = 32  # where the labels start, after PAD
    TEXT_ROOM = 8  # kept free after a label, before PAD
    SEPARATOR_INSET = 8  # a separator line's ends, inside PAD

    def __init__(
        self,
        root: tk.Misc,
        box: Box,
        items: Sequence[MenuItem | None],
        on_close: Callable[[], None],
    ) -> None:
        self._hovered: _Row | None = None
        self._rows: list[_Row] = []  # (y0, y1, item) for every non-separator item
        self._pad = pad = px(self.PAD)
        y = pad
        for item in items:
            h = px(self.SEPARATOR_HEIGHT) if item is SEPARATOR else px(self.ROW_HEIGHT)
            if item is not SEPARATOR:
                self._rows.append((y, y + h, item))
            y += h
        width = box[2] - box[0]
        super().__init__(root, width, y + pad, on_close)
        self._draw(items, width - self.BORDER)

        # <Enter> too: the pointer may land on a row and rest there with no <Motion>.
        for sequence in ("<Enter>", "<Motion>"):
            self.canvas.bind(sequence, lambda e: self._hover(self._row_at(e.y)))
        self.canvas.bind("<Leave>", lambda e: self._hover(None))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self._pick(self._row_at(e.y)))
        self.win.bind("<Up>", lambda e: self._step(-1))
        self.win.bind("<Down>", lambda e: self._step(1))
        self.win.bind("<Return>", lambda e: self._pick(self._hovered))
        self._show_under(box)

    def _draw(self, items: Sequence[MenuItem | None], width: int) -> None:
        canvas = self.canvas
        pad, row_height = self._pad, px(self.ROW_HEIGHT)
        separator_height, inset = px(self.SEPARATOR_HEIGHT), px(self.SEPARATOR_INSET)
        chip = ButtonStyle(fill=theme.SURFACE_HI, radius=px(self.CHIP_RADIUS))
        # The chip leaves a pixel above and below, so hovered rows never touch.
        self._chip_img = photo(
            canvas, button_pixels(width - 2 * pad, row_height - 2, chip, theme.SURFACE)
        )
        self._chip = canvas.create_image(pad, 0, anchor="nw", image=self._chip_img, state="hidden")
        font = tkfont.Font(font=theme.FONT)
        text_x = px(self.PAD + self.TEXT_X)
        y = pad
        for item in items:
            if item is SEPARATOR:
                middle_y = y + separator_height // 2
                canvas.create_line(
                    pad + inset,
                    middle_y,
                    width - pad - inset,
                    middle_y,
                    fill=theme.SURFACE_HI,
                    width=px(1),
                )
                y += separator_height
                continue
            middle_y = y + row_height // 2
            if item.checked:
                canvas.create_text(
                    px(self.PAD + self.CHECK_X),
                    middle_y,
                    text=GLYPH_CHECK,
                    font=theme.FONT_ICON,
                    fill=theme.ACCENT,
                )
            color = theme.OVERLAY if not item.enabled else theme.RED if item.danger else theme.TEXT
            label = elide(item.label, font, width - text_x - px(self.PAD + self.TEXT_ROOM))
            canvas.create_text(text_x, middle_y, text=label, anchor="w", font=font, fill=color)
            y += row_height
        canvas.tag_lower(self._chip)

    def _row_at(self, y: int) -> _Row | None:
        return next((row for row in self._rows if row[0] <= y < row[1]), None)

    def _hover(self, row: _Row | None) -> None:
        if row is not None and not row[2].enabled:
            row = None
        self._hovered = row
        if row is None:
            self.canvas.itemconfigure(self._chip, state="hidden")
            self.canvas.configure(cursor="")
        else:
            self.canvas.coords(self._chip, self._pad, row[0] + 1)
            self.canvas.itemconfigure(self._chip, state="normal")
            self.canvas.configure(cursor="hand2")

    def _step(self, direction: int) -> None:
        enabled = [row for row in self._rows if row[2].enabled]
        if not enabled:
            return
        if self._hovered not in enabled:
            self._hover(enabled[0 if direction > 0 else -1])
        else:
            self._hover(enabled[(enabled.index(self._hovered) + direction) % len(enabled)])

    def _pick(self, row: _Row | None) -> None:
        if row is None or not row[2].enabled:
            return
        self.close()
        row[2].command()


class SwatchPicker(_Dropdown):
    """A grid of colour swatches under `box`, the `selected` one ringed.

    Picking one calls on_pick(name) after closing. Arrow keys and Enter work too.
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    SWATCH = 18
    SPACING = 8
    PAD = 8
    RING = 3  # gap between a swatch and its ring
    RING_WIDTH = 2

    def __init__(
        self,
        root: tk.Misc,
        box: Box,
        colors: Sequence[tuple[str, str]],
        selected: str,
        on_pick: Callable[[str], None],
        on_close: Callable[[], None],
        per_row: int,
    ) -> None:
        self._colors, self._on_pick, self._per_row = colors, on_pick, per_row
        size, spacing, pad = px(self.SWATCH), px(self.SPACING), px(self.PAD)
        step = size + spacing
        columns = min(per_row, len(colors))
        rows = -(-len(colors) // per_row)
        width = 2 * pad + columns * step - spacing + self.BORDER
        super().__init__(root, width, 2 * pad + rows * step - spacing, on_close)
        canvas = self.canvas
        self._boxes: list[Box] = []
        self._imgs: list[tk.PhotoImage] = []
        for i, (_name, hex_color) in enumerate(colors):
            x = pad + (i % per_row) * step
            y = pad + (i // per_row) * step
            img = photo(
                canvas,
                button_pixels(
                    size, size, ButtonStyle(fill=hex_color, radius=size // 2), theme.SURFACE
                ),
            )
            self._imgs.append(img)
            canvas.create_image(x, y, anchor="nw", image=img)
            self._boxes.append((x, y, x + size, y + size))
        ring, ring_width = px(self.RING), px(self.RING_WIDTH)
        self._hover_ring = canvas.create_oval(
            0, 0, 0, 0, outline=theme.OVERLAY, width=ring_width, state="hidden"
        )
        chosen = next(i for i, (name, _) in enumerate(colors) if name == selected)
        x0, y0, x1, y1 = self._boxes[chosen]
        canvas.create_oval(
            x0 - ring, y0 - ring, x1 + ring, y1 + ring, outline=theme.TEXT, width=ring_width
        )
        self._hovered: int | None = None

        for sequence in ("<Enter>", "<Motion>"):
            canvas.bind(sequence, lambda e: self._hover(self._index_at(e)))
        canvas.bind("<Leave>", lambda e: self._hover(None))
        canvas.bind("<ButtonRelease-1>", lambda e: self._pick(self._index_at(e)))
        for key, delta in (("Left", -1), ("Right", 1), ("Up", -per_row), ("Down", per_row)):
            self.win.bind(f"<{key}>", partial(self._key_step, delta, chosen))
        self.win.bind("<Return>", lambda e: self._pick(self._hovered))
        self._show_under(box)

    def _index_at(self, e: tk.Event[tk.Canvas]) -> int | None:
        """The swatch under the pointer, counting the gaps around it (half a spacing each side)."""
        half = px(self.SPACING) // 2
        return next(
            (
                i
                for i, (x0, y0, x1, y1) in enumerate(self._boxes)
                if x0 - half <= e.x < x1 + half and y0 - half <= e.y < y1 + half
            ),
            None,
        )

    def _hover(self, index: int | None) -> None:
        self._hovered = index
        if index is None:
            self.canvas.itemconfigure(self._hover_ring, state="hidden")
            self.canvas.configure(cursor="")
            return
        x0, y0, x1, y1 = self._boxes[index]
        ring = px(self.RING)
        self.canvas.coords(self._hover_ring, x0 - ring, y0 - ring, x1 + ring, y1 + ring)
        self.canvas.itemconfigure(self._hover_ring, state="normal")
        self.canvas.configure(cursor="hand2")

    def _key_step(self, delta: int, start: int, _e: tk.Event[tk.Misc]) -> None:
        self._step(delta, start)

    def _step(self, delta: int, start: int) -> None:
        current = start if self._hovered is None else self._hovered
        self._hover((current + delta) % len(self._colors))

    def _pick(self, index: int | None) -> None:
        if index is None:
            return
        self.close()
        self._on_pick(self._colors[index][0])


class DropdownField(tk.Canvas):
    """A box showing the chosen option; a click lists the `options` ((value, label), ...)."""

    # Sizes at 100% display scaling, scaled with px() where used.
    HEIGHT = 36
    PAD_X = 10
    RADIUS = 8
    CHEVRON_X = 6  # the chevron's centre, before PAD_X from the right

    def __init__(
        self,
        parent: tk.Misc,
        options: Sequence[tuple[str, str]],
        value: str,
        *,
        width: int,
        background: str,
        on_pick: Callable[[str], None],
    ) -> None:
        self._height = height = px(self.HEIGHT)
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=background,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._choices, self.value, self._on_pick = options, value, on_pick
        self._width = width
        box = outlined_pixels(
            width, height, px(self.RADIUS), theme.SURFACE, theme.SURFACE_HI, background
        )
        self._img = photo(self, box)
        self.create_image(0, 0, anchor="nw", image=self._img)
        middle_y = height // 2
        self._text = self.create_text(
            px(self.PAD_X), middle_y, anchor="w", font=theme.FONT, fill=theme.TEXT
        )
        self._chevron = self.create_text(
            width - px(self.PAD_X + self.CHEVRON_X),
            middle_y,
            text=GLYPH_CHEVRON_DOWN,
            font=theme.FONT_ICON,
            fill=theme.SUBTEXT,
        )
        self._draw()
        self.bind("<ButtonRelease-1>", lambda e: self._open())

    def _draw(self) -> None:
        self.itemconfigure(self._text, text=dict(self._choices)[self.value])

    def _open(self) -> None:
        x, y = self.winfo_rootx(), self.winfo_rooty()
        items = [
            MenuItem(label, partial(self._pick, value), checked=value == self.value)
            for value, label in self._choices
        ]
        self.itemconfigure(self._chevron, text=GLYPH_CHEVRON_UP)
        PopupMenu(
            self.winfo_toplevel(),
            (x, y, x + self._width, y + self._height),
            items,
            on_close=self._closed,
        )

    def _closed(self) -> None:
        self.itemconfigure(self._chevron, text=GLYPH_CHEVRON_DOWN)

    def _pick(self, value: str) -> None:
        self.value = value
        self._draw()
        self._on_pick(value)


class ProfilePicker(tk.Canvas):
    """Full-width box showing the active profile; a click calls on_open(box).

    The owner opens a PopupMenu there and calls set_open(False) when it closes.
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    HEIGHT = 36
    PAD = 12
    ICON_X = 8  # the profile icon's centre, after PAD
    NAME_X = 26  # where the name starts, after PAD
    CHEVRON_X = 6  # the chevron's centre, before PAD from the right
    CHEVRON_ROOM = 22  # kept free for the chevron, before PAD from the right
    RADIUS = 8

    def __init__(self, parent: tk.Misc, *, width: int, on_open: Callable[[Box], None]) -> None:
        super().__init__(
            parent,
            width=width,
            height=px(self.HEIGHT),
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._width = width
        self._on_open = on_open
        self._hovered = self._open = False
        height = px(self.HEIGHT)
        radius = px(self.RADIUS)
        self._imgs = {
            fill: photo(self, button_pixels(width, height, ButtonStyle(fill, radius), theme.BG))
            for fill in (theme.SURFACE, theme.SURFACE_HI)
        }
        middle_y = height // 2
        self._box = self.create_image(0, 0, anchor="nw")
        self.create_text(
            px(self.PAD + self.ICON_X),
            middle_y,
            text=GLYPH_PROFILE,
            font=theme.FONT_ICON,
            fill=theme.SUBTEXT,
        )
        self._name_font = tkfont.Font(font=theme.FONT_BOLD)
        self._name_item = self.create_text(
            px(self.PAD + self.NAME_X), middle_y, anchor="w", font=self._name_font, fill=theme.TEXT
        )
        self._chevron = self.create_text(
            width - px(self.PAD + self.CHEVRON_X),
            middle_y,
            font=theme.FONT_ICON,
            fill=theme.SUBTEXT,
        )
        self._draw()

        self.bind("<Enter>", lambda e: self._set_hovered(True))
        self.bind("<Leave>", lambda e: self._set_hovered(False))
        self.bind("<ButtonRelease-1>", self._click)

    def set_name(self, name: str) -> None:
        room = self._width - px(self.PAD + self.NAME_X) - px(self.PAD + self.CHEVRON_ROOM)
        self.itemconfigure(self._name_item, text=elide(name, self._name_font, room))

    def set_open(self, is_open: bool) -> None:
        self._open = is_open
        self._draw()

    def _set_hovered(self, hovered: bool) -> None:
        self._hovered = hovered
        self._draw()

    def _draw(self) -> None:
        fill = theme.SURFACE_HI if self._hovered or self._open else theme.SURFACE
        self.itemconfigure(self._box, image=self._imgs[fill])
        glyph = GLYPH_CHEVRON_UP if self._open else GLYPH_CHEVRON_DOWN
        self.itemconfigure(self._chevron, text=glyph)

    def _click(self, e: tk.Event[tk.Canvas]) -> None:
        height = px(self.HEIGHT)
        if self._open or not (0 <= e.x < self._width and 0 <= e.y < height):
            return
        x, y = self.winfo_rootx(), self.winfo_rooty()
        self.set_open(True)
        self._on_open((x, y, x + self._width, y + height))
