"""The magnifier shown beside the pointer while a region is being selected."""

import tkinter as tk

from tibia_mirror import win32
from tibia_mirror.core.geometry import Rect, magnifier_source
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.dwm import Thumbnail
from tibia_mirror.ui import theme
from tibia_mirror.ui.scale import px
from tibia_mirror.ui.windows import keep_open


class Loupe:
    """A small window beside the pointer showing the game under it enlarged.

    The image is a DWM thumbnail, which covers anything the window draws, so the
    reticle is a second, see-through window on top. Neither takes the mouse.
    """

    SPAN = 11  # game pixels across; odd, so the pointer's pixel is the centre one
    # Sizes at 100% display scaling, scaled with px() in __init__.
    ZOOM = 6  # screen pixels per game pixel
    MARGIN = 7  # around the image, where the marks are drawn
    READOUT = 34  # height of the readout below: position, then selection size
    READOUT_LIFT = 2  # the readout sits this much above its band's centre
    OFFSET = 28  # from the pointer
    MARK = 4  # length of a mark
    MARK_WIDTH = 2
    MARK_GAP = 1  # between a mark and the image
    ARM_LENGTH = 10  # of the reticle's crosshair arms
    ARM_GAP = 3  # between the pixel's frame and the arms
    # The loupe's own 1px frame, and the reticle's outlines (1px white over 3px black,
    # framing exactly one enlarged pixel), stay as they are at any scaling.
    # Drawn nowhere in the reticle; Windows makes pixels of this colour transparent.
    SEE_THROUGH = "#ff00fe"

    def __init__(self, root: tk.Misc, game_hwnd: Hwnd, client: Rect) -> None:
        self._client = client  # the game's client area, a screen Rect
        self._zoom, self._margin, self._offset = px(self.ZOOM), px(self.MARGIN), px(self.OFFSET)
        view = self.SPAN * self._zoom
        readout = px(self.READOUT)
        self._width = 2 + 2 * self._margin + view
        self._height = 2 + 2 * self._margin + view + readout

        # 1px frame: the SURFACE_HI toplevel shows around the canvas.
        self.win = tk.Toplevel(root, bg=theme.SURFACE_HI)
        keep_open(self.win)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self._canvas = tk.Canvas(
            self.win,
            width=self._width - 2,
            height=self._height - 2,
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(padx=1, pady=1)
        self._marks = [
            self._canvas.create_line(0, 0, 0, 0, fill=theme.ACCENT, width=px(self.MARK_WIDTH))
            for _ in range(4)
        ]
        self._readout = self._canvas.create_text(
            self._width // 2 - 1,
            self._height - 2 - readout // 2 - px(self.READOUT_LIFT),
            font=theme.FONT_SMALL,
            fill=theme.TEXT,
            justify="center",
        )
        self.win.geometry(f"{self._width}x{self._height}+0+0")
        self.hwnd = win32.toplevel_hwnd(self.win)
        win32.set_alpha(self.hwnd, 1.0)
        win32.set_click_through(self.hwnd, True)
        self._thumb = Thumbnail(self.hwnd, game_hwnd)
        self._build_reticle(root, view)
        self._shown = False

    def _build_reticle(self, root: tk.Misc, view: int) -> None:
        """A see-through window over the image: a frame around the pixel, and crosshair arms.

        Each shape is drawn black under white, so it shows over any part of the game.
        """
        self._reticle = tk.Toplevel(root, bg=self.SEE_THROUGH)
        keep_open(self._reticle)
        self._reticle.withdraw()
        self._reticle.overrideredirect(True)
        self._reticle.attributes("-topmost", True)
        self._reticle.attributes("-transparentcolor", self.SEE_THROUGH)
        canvas = tk.Canvas(
            self._reticle,
            width=view,
            height=view,
            bg=self.SEE_THROUGH,
            highlightthickness=0,
            bd=0,
        )
        canvas.pack()
        self._reticle_canvas = canvas
        self._reticle_items: list[tuple[int, str]] = []  # (item, kind): kind picks _aim coords
        for color, width in (("#000000", 3), ("#ffffff", 1)):
            for kind in ("box", "up", "down", "left", "right"):
                if kind == "box":
                    item = canvas.create_rectangle(0, 0, 0, 0, outline=color, width=width)
                else:
                    item = canvas.create_line(0, 0, 0, 0, fill=color, width=width)
                self._reticle_items.append((item, kind))
        self._reticle.geometry(f"{view}x{view}+0+0")
        # Tk makes the window layered for -transparentcolor; add click-through on top.
        win32.set_click_through(win32.toplevel_hwnd(self._reticle), True)

    def _aim(self, x0: int, y0: int) -> None:
        """Frame the enlarged pixel whose top-left is (x0, y0) in the image."""
        size, gap, arm = self._zoom, px(self.ARM_GAP), px(self.ARM_LENGTH)  # size: one pixel
        x1, y1 = x0 + size, y0 + size  # the pixel spans [x0, x1) x [y0, y1)
        center_x, center_y = x0 + size // 2, y0 + size // 2
        coords = {
            "box": (x0 - 2, y0 - 2, x1 + 1, y1 + 1),
            "up": (center_x, y0 - 2 - gap - arm, center_x, y0 - 2 - gap),
            "down": (center_x, y1 + 1 + gap, center_x, y1 + 1 + gap + arm),
            "left": (x0 - 2 - gap - arm, center_y, x0 - 2 - gap, center_y),
            "right": (x1 + 1 + gap, center_y, x1 + 1 + gap + arm, center_y),
        }
        for item, kind in self._reticle_items:
            self._reticle_canvas.coords(item, *coords[kind])

    def update(self, x_root: int, y_root: int, selection: tuple[int, int] | None = None) -> None:
        """Follow the pointer at (x_root, y_root); `selection` is the dragged size, if any."""
        client = self._client
        game_x, game_y = x_root - client.x, y_root - client.y  # the pointer in game pixels
        source = magnifier_source(game_x, game_y, self.SPAN, client.w, client.h)
        zoom, margin = self._zoom, self._margin
        # The thumbnail is drawn in the toplevel's client area: offset by the 1px frame.
        left = top = 1 + margin
        self._thumb.show(source, Rect(left, top, source.w * zoom, source.h * zoom))

        # The pointer's pixel in the enlarged image: off-centre near the game's edges.
        view = self.SPAN * zoom
        pixel_x = self._clamp((game_x - source.x) * zoom, view)
        pixel_y = self._clamp((game_y - source.y) * zoom, view)
        self._aim(pixel_x, pixel_y)
        # Canvas coordinates are 1px inside the toplevel's.
        center_x = margin + pixel_x + zoom // 2
        center_y = margin + pixel_y + zoom // 2
        near, far = margin, margin + view  # the image's edges on the canvas
        mark, gap = px(self.MARK), px(self.MARK_GAP)
        for item, coords in zip(
            self._marks,
            (
                (center_x, near - mark - gap, center_x, near - gap),  # above
                (center_x, far + gap, center_x, far + mark + gap),  # below
                (near - mark - gap, center_y, near - gap, center_y),  # left
                (far + gap, center_y, far + mark + gap, center_y),  # right
            ),
            strict=True,
        ):
            self._canvas.coords(item, *coords)

        # Two lines, so the loupe can stay narrow; the second is blank until dragging.
        text = f"{game_x}, {game_y}\n"
        if selection is not None:
            text += f"{selection[0]} × {selection[1]}"
        self._canvas.itemconfigure(self._readout, text=text)
        self._place(x_root, y_root)
        if not self._shown:
            self.win.deiconify()
            self._reticle.deiconify()  # after the loupe, so it stays above it
            self._shown = True

    def destroy(self) -> None:
        try:
            self._thumb.close()
        finally:
            self._reticle.destroy()
            self.win.destroy()

    def _clamp(self, value: int, limit: int) -> int:
        """Keep a pixel's left/top edge inside the image."""
        return min(max(value, 0), limit - self._zoom)

    def _place(self, x_root: int, y_root: int) -> None:
        """Below-right of the pointer, flipped to the other side near its monitor's edges."""
        area = win32.work_area_at((x_root, y_root))
        offset = self._offset
        x = x_root + offset
        if x + self._width > area.right:
            x = x_root - offset - self._width
        y = y_root + offset
        if y + self._height > area.bottom:
            y = y_root - offset - self._height
        self.win.geometry(f"+{x}+{y}")
        image = 1 + self._margin  # the image's offset inside the loupe window
        self._reticle.geometry(f"+{x + image}+{y + image}")
