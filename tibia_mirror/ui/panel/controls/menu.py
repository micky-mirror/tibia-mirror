"""Dropdowns: the colour picker."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence
from functools import partial

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels
from tibia_mirror.ui.base.scale import px
from tibia_mirror.winapi import dwm, win32


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
