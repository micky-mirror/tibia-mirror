"""Custom Tk widgets, mostly drawn on a canvas for rounded, anti-aliased shapes."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Protocol

from tibia_mirror.config import FRAME_COLORS, FRAME_COLORS_PER_ROW, MIN_OPACITY, OPACITY_STEP
from tibia_mirror.core.geometry import Box, Point, scroll_fraction, scroll_thumb
from tibia_mirror.core.regions import clamp_opacity
from tibia_mirror.core.timers import KeyCombo, clock
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels, margins, outlined_pixels
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.menu import SwatchPicker
from tibia_mirror.ui.slider import SliderDrawing
from tibia_mirror.ui.tooltip import Tooltip


class RaisedButton(tk.Canvas):
    """Rounded button with a soft shadow, and hover, pressed and disabled looks.

    The canvas is bigger by `self.margins` (room for the shadow); offset the widget
    by them so the button body lines up.
    """

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], object],  # what it returns is ignored
        *,
        width: int,
        height: int,
        style: ButtonStyle,
        hover_fill: str,
        font: theme.FontSpec,
        fg: str,
        background: str,
    ) -> None:
        self.margins = margins(style)
        super().__init__(
            parent,
            width=self.margins.left + width + self.margins.right,
            height=self.margins.top + height + self.margins.bottom,
            bg=background,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._command = command
        self._fg = fg
        hover = replace(style, fill=hover_fill)
        disabled = replace(style, fill=theme.SURFACE)
        self._images = {
            "normal": photo(self, button_pixels(width, height, style, background)),
            "hover": photo(self, button_pixels(width, height, hover, background)),
            "pressed": photo(self, button_pixels(width, height, hover, background, True)),
            "disabled": photo(self, button_pixels(width, height, disabled, background)),
        }
        self._image = self.create_image(0, 0, anchor="nw", image=self._images["normal"])
        self._text_pos = (self.margins.left + width / 2, self.margins.top + height / 2)
        self._text = self.create_text(*self._text_pos, text=text, font=font, fill=fg)
        self._hovered = self._pressed = False
        self._enabled = True

        self.bind("<Enter>", lambda e: self._update(hovered=True))
        self.bind("<Leave>", lambda e: self._update(hovered=False))
        self.bind("<ButtonPress-1>", lambda e: self._update(pressed=True))
        self.bind("<ButtonRelease-1>", self._release)

    def set_enabled(self, enabled: bool) -> None:
        if enabled != self._enabled:
            self._enabled = enabled
            self._pressed = False
            self.configure(cursor="hand2" if enabled else "")
            self.itemconfigure(self._text, fill=self._fg if enabled else theme.OVERLAY)
            self._update()

    def _release(self, _event: tk.Event[tk.Canvas]) -> None:
        fire = self._pressed and self._hovered and self._enabled
        self._update(pressed=False)
        if fire:
            self._command()

    def _update(self, hovered: bool | None = None, pressed: bool | None = None) -> None:
        if hovered is not None:
            self._hovered = hovered
        if pressed is not None:
            self._pressed = pressed
        down = self._pressed and self._hovered and self._enabled
        if not self._enabled:
            state = "disabled"
        else:
            state = "pressed" if down else "hover" if self._hovered else "normal"
        self.itemconfigure(self._image, image=self._images[state])
        x, y = self._text_pos
        self.coords(self._text, x, y + (1 if down else 0))


class TextField(tk.Canvas):
    """Rounded single-line text entry; `self.entry` is the tk.Entry inside.

    Its border is ACCENT while focused and RED while set_error(True).
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    HEIGHT = 36
    PAD_X = 10
    RADIUS = 8

    def __init__(
        self, parent: tk.Misc, textvariable: tk.StringVar, *, width: int, background: str
    ) -> None:
        height, pad_x = px(self.HEIGHT), px(self.PAD_X)
        super().__init__(
            parent, width=width, height=height, bg=background, highlightthickness=0, bd=0
        )
        radius = px(self.RADIUS)
        self._imgs = {
            state: photo(
                self,
                outlined_pixels(width, height, radius, theme.SURFACE, border, background),
            )
            for state, border in (
                ("normal", theme.SURFACE_HI),
                ("focus", theme.ACCENT),
                ("error", theme.RED),
            )
        }
        self._box = self.create_image(0, 0, anchor="nw")
        self.entry = tk.Entry(
            self,
            textvariable=textvariable,
            font=theme.FONT,
            bg=theme.SURFACE,
            fg=theme.TEXT,
            insertbackground=theme.TEXT,
            selectbackground=theme.ACCENT,
            selectforeground=theme.ON_ACCENT,
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        self.create_window(
            pad_x,
            height // 2,
            window=self.entry,
            anchor="w",
            width=width - 2 * pad_x,
        )
        self._focused = self._error = False
        self.entry.bind("<FocusIn>", lambda e: self._set(focused=True), add="+")
        self.entry.bind("<FocusOut>", lambda e: self._set(focused=False), add="+")
        # A click on the padding focuses the entry too.
        self.bind("<ButtonPress-1>", lambda e: self.entry.focus_set())
        self.configure(cursor="xterm")
        self._draw()

    def set_error(self, error: bool) -> None:
        self._set(error=error)

    def _set(self, focused: bool | None = None, error: bool | None = None) -> None:
        if focused is not None:
            self._focused = focused
        if error is not None:
            self._error = error
        self._draw()

    def _draw(self) -> None:
        state = "error" if self._error else "focus" if self._focused else "normal"
        self.itemconfigure(self._box, image=self._imgs[state])


class CheckBox(tk.Canvas):
    """A check box with its label; clicking anywhere on it toggles `value`.

    The label wraps to `width`, so a long translation takes a second line.
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    BOX_SIZE = 16
    GAP = 8  # between the box and its label
    RADIUS = 4

    def __init__(
        self, parent: tk.Misc, text: str, *, value: bool = False, background: str, width: int
    ) -> None:
        font = tkfont.Font(font=theme.FONT)
        size, gap, radius = px(self.BOX_SIZE), px(self.GAP), px(self.RADIUS)
        text_width = width - size - gap
        super().__init__(
            parent, width=width, height=1, bg=background, highlightthickness=0, bd=0, cursor="hand2"
        )
        self._imgs = {
            (False, False): photo(
                self, outlined_pixels(size, size, radius, theme.SURFACE, theme.OVERLAY, background)
            ),
            (False, True): photo(
                self, outlined_pixels(size, size, radius, theme.SURFACE, theme.SUBTEXT, background)
            ),
            (True, False): photo(
                self,
                button_pixels(size, size, ButtonStyle(theme.ACCENT, radius), background),
            ),
            (True, True): photo(
                self,
                button_pixels(size, size, ButtonStyle(theme.ACCENT_HI, radius), background),
            ),
        }
        label = self.create_text(
            size + gap,
            0,
            text=text,
            anchor="nw",
            width=text_width,
            font=font,
            fill=theme.TEXT,
        )
        height = max(size, self.bbox(label)[3])
        self.configure(height=height)
        # The box sits beside the first line of the label.
        middle_y = font.metrics("linespace") // 2
        self._box = self.create_image(0, middle_y, anchor="w")
        self._check = self.create_text(
            size // 2, middle_y, text=GLYPH_CHECK, font=theme.FONT_ICON_SMALL, fill=theme.ON_ACCENT
        )
        self.value = value
        self._hovered = False
        self._draw()
        self.bind("<Enter>", lambda e: self._set_hovered(True))
        self.bind("<Leave>", lambda e: self._set_hovered(False))
        self.bind("<ButtonRelease-1>", self._click)

    def _set_hovered(self, hovered: bool) -> None:
        self._hovered = hovered
        self._draw()

    def _click(self, e: tk.Event[tk.Canvas]) -> None:
        if 0 <= e.x < self.winfo_width() and 0 <= e.y < self.winfo_height():
            self.value = not self.value
            self._draw()

    def _draw(self) -> None:
        self.itemconfigure(self._box, image=self._imgs[self.value, self._hovered])
        self.itemconfigure(self._check, state="normal" if self.value else "hidden")


# Segoe MDL2 Assets code points (FONT_ICON).
GLYPH_CHECK = "\ue73e"
GLYPH_LOCKED = "\ue72e"
GLYPH_UNLOCKED = "\ue785"
GLYPH_SHOWN = "\ue890"
GLYPH_HIDDEN = "\ued1a"
GLYPH_TIMER = "\ue916"

# A tooltip's (title, detail): what a click does, then what that means.
Tip = tuple[str, str]


class _CardControl(Protocol):
    """What RegionCard needs from anything clickable drawn on it."""

    command: Callable[[], None]
    tip: Tip

    def contains(self, x: float, y: float) -> bool: ...

    def screen_box(self) -> Box: ...

    def set_hovered(self, hovered: bool) -> None: ...


class _CardButton:
    """Square icon button on a card canvas, with a rounded chip behind it on hover."""

    CHIP_RADIUS = 6  # at 100% display scaling

    def __init__(
        self,
        canvas: tk.Canvas,
        center_x: float,
        center_y: float,
        size: int,
        chip_fill: str,
        command: Callable[[], None],
    ) -> None:
        self._canvas, self.command = canvas, command
        half = size / 2
        self._box = (center_x - half, center_y - half, center_x + half, center_y + half)
        chip = ButtonStyle(fill=chip_fill, radius=px(self.CHIP_RADIUS))
        self._chip_img = photo(canvas, button_pixels(size, size, chip, theme.SURFACE))
        self._chip = canvas.create_image(center_x, center_y, image=self._chip_img, state="hidden")
        self._glyph = canvas.create_text(center_x, center_y)
        self._hovered = False
        self._colors = (theme.SUBTEXT, theme.TEXT)
        self.tip: Tip = ("", "")

    def show(
        self, glyph: str, font: theme.FontSpec, color: str, hover_color: str, tip: Tip
    ) -> None:
        self._colors = (color, hover_color)
        self.tip = tip
        self._canvas.itemconfigure(self._glyph, text=glyph, font=font)
        self._paint()

    def contains(self, x: float, y: float) -> bool:
        x0, y0, x1, y1 = self._box
        return x0 <= x < x1 and y0 <= y < y1

    def screen_box(self) -> Box:
        x0, y0, x1, y1 = self._box
        origin_x, origin_y = self._canvas.winfo_rootx(), self._canvas.winfo_rooty()
        return (
            round(origin_x + x0),
            round(origin_y + y0),
            round(origin_x + x1),
            round(origin_y + y1),
        )

    def set_hovered(self, hovered: bool) -> None:
        if hovered != self._hovered:
            self._hovered = hovered
            self._paint()

    def _paint(self) -> None:
        self._canvas.itemconfigure(self._chip, state="normal" if self._hovered else "hidden")
        self._canvas.itemconfigure(self._glyph, fill=self._colors[self._hovered])


class _CardLink:
    """A text item on a card canvas that works like a button (accent on hover)."""

    # A little slack around the glyphs, at 100% display scaling.
    SLACK_X = 3
    SLACK_Y = 2

    def __init__(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        text: str,
        font: tkfont.Font,
        command: Callable[[], None],
        tip: Tip,
    ) -> None:
        self._canvas, self.command, self.tip = canvas, command, tip
        self._item = canvas.create_text(x, y, text=text, anchor="w", font=font, fill=theme.SUBTEXT)
        x0, y0, x1, y1 = canvas.bbox(self._item)
        slack_x, slack_y = px(self.SLACK_X), px(self.SLACK_Y)
        self._box = (x0 - slack_x, y0 - slack_y, x1 + slack_x, y1 + slack_y)

    def contains(self, x: float, y: float) -> bool:
        x0, y0, x1, y1 = self._box
        return x0 <= x < x1 and y0 <= y < y1

    def screen_box(self) -> Box:
        x0, y0, x1, y1 = self._box
        origin_x, origin_y = self._canvas.winfo_rootx(), self._canvas.winfo_rooty()
        return (
            round(origin_x + x0),
            round(origin_y + y0),
            round(origin_x + x1),
            round(origin_y + y1),
        )

    def set_hovered(self, hovered: bool) -> None:
        self._canvas.itemconfigure(self._item, fill=theme.ACCENT if hovered else theme.SUBTEXT)


class _CardDot:
    """The frame-colour dot on a card, with a rounded chip behind it on hover."""

    # Sizes at 100% display scaling, scaled with px() where used.
    DOT_SIZE = 10
    SIZE = 22  # the hover chip, and the clickable area
    CHIP_RADIUS = 6

    def __init__(
        self,
        canvas: tk.Canvas,
        center_x: float,
        center_y: float,
        color: str,
        command: Callable[[], None],
        tip: Tip,
    ) -> None:
        self._canvas, self.command, self.tip = canvas, command, tip
        size, dot_size = px(self.SIZE), px(self.DOT_SIZE)
        half = size / 2
        self._box = (center_x - half, center_y - half, center_x + half, center_y + half)
        chip = ButtonStyle(fill=theme.SURFACE_HI, radius=px(self.CHIP_RADIUS))
        self._chip_img = photo(canvas, button_pixels(size, size, chip, theme.SURFACE))
        self._chip = canvas.create_image(center_x, center_y, image=self._chip_img, state="hidden")
        dot = ButtonStyle(fill=color, radius=dot_size // 2)
        self._dot_imgs = {
            hovered: photo(
                canvas,
                button_pixels(
                    dot_size,
                    dot_size,
                    dot,
                    theme.SURFACE_HI if hovered else theme.SURFACE,
                ),
            )
            for hovered in (False, True)
        }
        self._dot = canvas.create_image(center_x, center_y, image=self._dot_imgs[False])

    def contains(self, x: float, y: float) -> bool:
        x0, y0, x1, y1 = self._box
        return x0 <= x < x1 and y0 <= y < y1

    def screen_box(self) -> Box:
        x0, y0, x1, y1 = self._box
        origin_x, origin_y = self._canvas.winfo_rootx(), self._canvas.winfo_rooty()
        return (
            round(origin_x + x0),
            round(origin_y + y0),
            round(origin_x + x1),
            round(origin_y + y1),
        )

    def set_hovered(self, hovered: bool) -> None:
        self._canvas.itemconfigure(self._chip, state="normal" if hovered else "hidden")
        self._canvas.itemconfigure(self._dot, image=self._dot_imgs[hovered])


class RegionCard(tk.Canvas):
    """A region's card: name, size, toggles and remove on top, opacity slider below.

    Drawn on one canvas and hit-tested by position, so Enter/Leave stay clean.
    Call release_hover() before destroying it, or its mirror stays highlighted.
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    HEIGHT = 62
    PAD = 14  # same inset as the settings cards
    RADIUS = 8
    TOP_Y = 20
    SLIDER_Y = 44
    BUTTON_SIZE = 26
    BUTTON_GAP = 2
    BUTTONS_INSET = 8  # from the card's right edge to the last button
    DOT_X = 4  # the colour dot's centre, after PAD
    NAME_GAP = 4  # from the colour dot's chip to the name
    TEXT_GAP = 8  # between the name, the size and the buttons
    READOUT_WIDTH = 48

    def __init__(
        self,
        parent: tk.Misc,
        name: str,
        size_text: str,
        opacity: float,
        *,
        hidden: bool,
        locked: bool,
        color: str,
        timer_on: bool,
        timer_alert: int,
        width: int,
        on_remove: Callable[[], None],
        on_hover: Callable[[bool], None],
        on_opacity: Callable[[float], None],
        on_adjust: Callable[[bool], None],
        on_rename: Callable[[Point], None],
        on_resize: Callable[[Point], None],
        on_color: Callable[[str], None],
        on_timer: Callable[[Point], None],
        on_hidden: Callable[[bool], None],
        on_locked: Callable[[bool], None],
    ) -> None:
        super().__init__(
            parent, width=width, height=px(self.HEIGHT), bg=theme.BG, highlightthickness=0, bd=0
        )
        self._on_remove, self._on_hover = on_remove, on_hover
        self._on_opacity, self._on_adjust = on_opacity, on_adjust
        self._on_rename = on_rename
        self._on_hidden, self._on_locked = on_hidden, on_locked
        self._on_resize = on_resize
        self._on_color = on_color
        self._on_timer = on_timer
        self._timer_on, self._timer_alert = timer_on, timer_alert
        self._color = color
        self._hidden, self._locked = hidden, locked

        card = ButtonStyle(fill=theme.SURFACE, radius=px(self.RADIUS))
        self._card_img = photo(self, button_pixels(width, px(self.HEIGHT), card, theme.BG))
        self.create_image(0, 0, anchor="nw", image=self._card_img)

        self._build_top_row(name, size_text, width)
        self._build_slider(opacity, width)

        self._inside = self._dragging = False
        self._pressed_button: _CardControl | None = None
        self._tip_button: _CardControl | None = None  # under the pointer, for its tooltip
        # Mastered by the window, not the card, so a pending hint outlives the card
        # only until <Destroy> below cancels it.
        self._tooltip = Tooltip(self.winfo_toplevel())
        self._rename_pending = False
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Motion>", self._motion)
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Double-Button-1>", self._double_click)
        self.bind("<Destroy>", lambda e: self._tooltip.hide())

    # ---- construction -------------------------------------------------------
    def _build_top_row(self, name: str, size_text: str, width: int) -> None:
        # Buttons right to left: remove, lock, show/hide, timer.
        size, top_y, text_gap = px(self.BUTTON_SIZE), px(self.TOP_Y), px(self.TEXT_GAP)
        step = size + px(self.BUTTON_GAP)
        right = width - px(self.BUTTONS_INSET) - size / 2
        centers_x = [right - i * step for i in range(4)]
        self._remove = _CardButton(self, centers_x[0], top_y, size, theme.RED, self._on_remove)
        self._remove.show(
            "✕", theme.FONT, theme.SUBTEXT, theme.ON_ACCENT, (tr("Remove region"), "")
        )
        self._lock = _CardButton(
            self, centers_x[1], top_y, size, theme.SURFACE_HI, self._toggle_locked
        )
        self._eye = _CardButton(
            self, centers_x[2], top_y, size, theme.SURFACE_HI, self._toggle_hidden
        )
        self._clock = _CardButton(
            self,
            centers_x[3],
            top_y,
            size,
            theme.SURFACE_HI,
            lambda: self._on_timer(self._center()),
        )
        dot_cx = px(self.PAD + self.DOT_X)
        self._dot = _CardDot(
            self,
            dot_cx,
            top_y,
            theme.frame_color(self._color),
            self._pick_color,
            (tr("Frame colour"), ""),
        )
        name_x = dot_cx + px(_CardDot.SIZE) / 2 + px(self.NAME_GAP)
        name_font, size_font = tkfont.Font(font=theme.FONT_BOLD), tkfont.Font(font=theme.FONT)
        buttons_x = centers_x[3] - size / 2 - text_gap
        name_room = buttons_x - name_x - text_gap - size_font.measure(size_text)
        shown = elide(name, name_font, name_room)
        self._name_item = self.create_text(name_x, top_y, text=shown, anchor="w", font=name_font)
        self._size = _CardLink(
            self,
            name_x + name_font.measure(shown) + text_gap,
            top_y,
            size_text,
            size_font,
            lambda: self._on_resize(self._center()),
            (tr("Edit region"), tr("Position, size and zoom.")),
        )
        self._buttons: tuple[_CardControl, ...] = (
            self._remove,
            self._lock,
            self._eye,
            self._clock,
            self._size,
            self._dot,
        )
        self._draw_toggles()
        self._draw_timer()

    def _build_slider(self, opacity: float, width: int) -> None:
        pad, slider_y = px(self.PAD), px(self.SLIDER_Y)
        self._slider = SliderDrawing(
            self,
            pad,
            width - pad - px(self.READOUT_WIDTH),
            slider_y,
            clamp_opacity(opacity),
            lo=0.0,
            hi=1.0,
            step=OPACITY_STEP,
            floor=MIN_OPACITY,
        )
        self._readout = self.create_text(
            width - pad, slider_y, anchor="e", font=theme.FONT, fill=theme.SUBTEXT
        )
        self._draw_readout()

    # ---- drawing ------------------------------------------------------------
    def _draw_readout(self) -> None:
        self.itemconfigure(self._readout, text=f"{round(self._slider.value * 100)}%")

    def _draw_timer(self) -> None:
        if self._timer_on:
            tip = (tr("Timer"), tr("On: alerts after {time}.", time=clock(self._timer_alert)))
            self._clock.show(GLYPH_TIMER, theme.FONT_ICON, theme.ACCENT, theme.ACCENT, tip)
        else:
            tip = (tr("Timer"), tr("Counts time since you click this region or press its key."))
            self._clock.show(GLYPH_TIMER, theme.FONT_ICON, theme.SUBTEXT, theme.TEXT, tip)

    def _draw_toggles(self) -> None:
        """Toggles in their non-default state (hidden, locked) are drawn in the accent colour."""
        if self._locked:
            tip = (
                tr("Unlock mirror"),
                tr("Lets you move it again. Clicks land on the mirror."),
            )
            self._lock.show(GLYPH_LOCKED, theme.FONT_ICON, theme.ACCENT, theme.ACCENT, tip)
        else:
            tip = (
                tr("Lock mirror"),
                tr("Pins it in place. Clicks pass through it to the game."),
            )
            self._lock.show(GLYPH_UNLOCKED, theme.FONT_ICON, theme.SUBTEXT, theme.TEXT, tip)
        if self._hidden:
            tip = (tr("Show mirror"), "")
            self._eye.show(GLYPH_HIDDEN, theme.FONT_ICON, theme.ACCENT, theme.ACCENT, tip)
        else:
            tip = (tr("Hide mirror"), tr("It stays in the profile; show it again any time."))
            self._eye.show(GLYPH_SHOWN, theme.FONT_ICON, theme.SUBTEXT, theme.TEXT, tip)
        self.itemconfigure(self._name_item, fill=theme.SUBTEXT if self._hidden else theme.TEXT)

    # ---- hit testing --------------------------------------------------------
    def _button_at(self, e: tk.Event[tk.Canvas]) -> _CardControl | None:
        return next((button for button in self._buttons if button.contains(e.x, e.y)), None)

    def _in_slider(self, e: tk.Event[tk.Canvas]) -> bool:
        return self._slider.contains(e.x, e.y)

    # ---- events -------------------------------------------------------------
    def _enter(self, e: tk.Event[tk.Canvas]) -> None:
        self._inside = True
        if not self._dragging:
            self._on_hover(True)
        # The pointer may land straight on a button and rest there with no <Motion>.
        self._motion(e)

    def _leave(self, _e: tk.Event[tk.Canvas]) -> None:
        self._inside = False
        for card_button in self._buttons:
            card_button.set_hovered(False)
        self._set_tip_button(None)
        # Mid-drag the pointer may wander off the card; stay "hovered" until release.
        if not self._dragging:
            self._slider.set_active(False)
            self.configure(cursor="")
            self._on_hover(False)

    def _motion(self, e: tk.Event[tk.Canvas]) -> None:
        button, on_slider = self._button_at(e), self._in_slider(e)
        for card_button in self._buttons:
            card_button.set_hovered(card_button is button)
        self._set_tip_button(button)
        self._slider.set_active(on_slider or self._dragging)
        self.configure(cursor="hand2" if button or on_slider else "")

    def _press(self, e: tk.Event[tk.Canvas]) -> None:
        button = self._button_at(e)
        # Like native tooltips: a click dismisses the hint until the pointer leaves the button.
        self._tooltip.hide()
        if button:
            self._pressed_button = button
        elif self._in_slider(e):
            self._dragging = True
            self._slider.set_active(True)
            self._on_adjust(True)
            self._slide_to(e.x)

    def _drag(self, e: tk.Event[tk.Canvas]) -> None:
        if self._dragging:
            self._slide_to(e.x)

    def _release(self, e: tk.Event[tk.Canvas]) -> None:
        if self._dragging:
            self._dragging = False
            self._on_adjust(False)
            if not self._inside:
                self._slider.set_active(False)
                self.configure(cursor="")
                self._on_hover(False)
        elif self._pressed_button:
            button, self._pressed_button = self._pressed_button, None
            if self._button_at(e) is button:
                # May destroy this card (remove), so nothing may follow it.
                button.command()
        elif self._rename_pending:
            # Opened on release: a dialog appearing under a held button would
            # see the rest of the click as a drag-select in its entry.
            self._rename_pending = False
            self._on_rename(self._center())

    def _double_click(self, e: tk.Event[tk.Canvas]) -> None:
        if self._button_at(e) or self._in_slider(e):
            # Tk sends the second press here instead of to _press; treat it as one.
            self._press(e)
            return
        self._rename_pending = True

    def _set_tip_button(self, button: _CardControl | None) -> None:
        if button is not self._tip_button:
            self._tip_button = button
            if button:
                title, detail = button.tip
                self._tooltip.show(title, button.screen_box(), detail)
            else:
                self._tooltip.hide()

    def _toggle_hidden(self) -> None:
        self._hidden = not self._hidden
        self._draw_toggles()
        self._on_hidden(self._hidden)

    def _toggle_locked(self) -> None:
        self._locked = not self._locked
        self._draw_toggles()
        self._on_locked(self._locked)

    def _pick_color(self) -> None:
        SwatchPicker(
            self.winfo_toplevel(),
            self._dot.screen_box(),
            [(name, theme.frame_color(name)) for name in FRAME_COLORS],
            self._color,
            on_pick=self._on_color,
            on_close=lambda: None,
            per_row=FRAME_COLORS_PER_ROW,
        )

    def _center(self) -> Point:
        return (
            self.winfo_rootx() + self.winfo_width() // 2,
            self.winfo_rooty() + self.winfo_height() // 2,
        )

    def release_hover(self) -> None:
        if self._inside or self._dragging:
            self._inside = self._dragging = False
            self._on_hover(False)

    def _slide_to(self, x: int) -> None:
        value = self._slider.value_at(x)
        if value != self._slider.value:
            self._slider.set_value(value)
            self._draw_readout()
            self._on_opacity(value)


class SegmentedDrawing:
    """Options side by side in a rounded track, the chosen one on an accent pill.

    Drawn on `canvas` with its right edge at x1, centred on `middle_y`. The owner
    handles the mouse with at() and redraws with draw().
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    HEIGHT = 28
    INSET = 2  # track padding around the pills
    PAD_X = 14  # text padding inside a pill
    TRACK_RADIUS = 8
    PILL_RADIUS = 6

    @classmethod
    def _widths(cls, options: Sequence[tuple[str, str]]) -> list[int]:
        font = tkfont.Font(font=theme.FONT)
        return [font.measure(text) + 2 * px(cls.PAD_X) for _, text in options]

    @classmethod
    def measure(cls, options: Sequence[tuple[str, str]]) -> int:
        return sum(cls._widths(options)) + 2 * px(cls.INSET)

    def __init__(
        self,
        canvas: tk.Canvas,
        x1: int,
        middle_y: int,
        options: Sequence[tuple[str, str]],
        background: str | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        background = theme.SURFACE if background is None else background
        self._canvas = canvas
        widths = self._widths(options)
        self.width = max(width or 0, self.measure(options))
        extra = self.width - self.measure(options)
        widths = [w + extra // len(widths) for w in widths]
        widths[-1] += extra % len(widths)
        self.height = height or px(self.HEIGHT)
        x0, y0 = x1 - self.width, middle_y - self.height // 2
        track = ButtonStyle(fill=theme.SURFACE_HI, radius=px(self.TRACK_RADIUS))
        self._track_img = photo(canvas, button_pixels(self.width, self.height, track, background))
        canvas.create_image(x0, y0, anchor="nw", image=self._track_img)
        inset = px(self.INSET)
        pill_h = self.height - 2 * inset
        pill = ButtonStyle(fill=theme.ACCENT, radius=px(self.PILL_RADIUS))
        self._segments: list[tuple[str, Box, tk.PhotoImage]] = []  # (value, box, pill image)
        x = x0 + inset
        for (value, _text), w in zip(options, widths, strict=True):
            img = photo(canvas, button_pixels(w, pill_h, pill, theme.SURFACE_HI))
            box = (x, y0 + inset, x + w, y0 + inset + pill_h)
            self._segments.append((value, box, img))
            x += w
        self._pill = canvas.create_image(0, 0, anchor="nw")
        self._texts = {
            value: canvas.create_text(
                (box[0] + box[2]) / 2, middle_y, text=text, font=theme.FONT, fill=theme.SUBTEXT
            )
            for (value, box, _), (_, text) in zip(self._segments, options, strict=True)
        }

    def at(self, x: int, y: int) -> str | None:
        """The option under (x, y), or None."""
        return next(
            (
                option
                for option, (x0, y0, x1, y1), _label in self._segments
                if x0 <= x < x1 and y0 <= y < y1
            ),
            None,
        )

    def draw(self, selected: str, hovered: str | None) -> None:
        for value, box, img in self._segments:
            if value == selected:
                self._canvas.coords(self._pill, box[0], box[1])
                self._canvas.itemconfigure(self._pill, image=img)
                color = theme.ON_ACCENT
            else:
                color = theme.TEXT if value == hovered else theme.SUBTEXT
            self._canvas.itemconfigure(self._texts[value], fill=color)


class ChoiceBar(tk.Canvas):
    """A standalone SegmentedDrawing: click an option to choose it (`value`)."""

    def __init__(
        self,
        parent: tk.Misc,
        options: Sequence[tuple[str, str]],
        value: str,
        *,
        background: str,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        width = max(width or 0, SegmentedDrawing.measure(options))
        height = height or px(SegmentedDrawing.HEIGHT)
        super().__init__(
            parent, width=width, height=height, bg=background, highlightthickness=0, bd=0
        )
        self.value = value
        self._drawing = SegmentedDrawing(
            self, width, height // 2, options, background, width=width, height=height
        )
        self._hovered: str | None = None
        self._drawing.draw(value, None)
        for sequence in ("<Enter>", "<Motion>"):
            self.bind(sequence, lambda e: self._hover(self._drawing.at(e.x, e.y)))
        self.bind("<Leave>", lambda e: self._hover(None))
        self.bind("<ButtonRelease-1>", self._click)

    def _hover(self, option: str | None) -> None:
        if option != self._hovered:
            self._hovered = option
            self._drawing.draw(self.value, option)
            self.configure(cursor="hand2" if option not in (None, self.value) else "")

    def _click(self, e: tk.Event[tk.Canvas]) -> None:
        option = self._drawing.at(e.x, e.y)
        if option is not None:
            self.value = option
            self._drawing.draw(option, option)
            self.configure(cursor="")


class KeyField(tk.Canvas):
    """Records a key combination: `value` is (vk, modifiers) or None.

    Click it, then press the keys; held modifiers show as "Ctrl+Shift+...". Escape
    keeps the old one and ✕ clears it. on_change(value) runs after each change.
    """

    MODIFIER_KEYSYMS = frozenset(
        {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Meta_L", "Meta_R"}
    )

    # Sizes at 100% display scaling, scaled with px() where used.
    HEIGHT = 36
    PAD_X = 10
    RADIUS = 8
    CLEAR = 24  # the clear button's width
    CLEAR_INSET = 4  # from the field's right edge to the clear button
    CLEAR_SLACK = 12  # clicks this far left of the ✕'s centre still clear the key

    def __init__(
        self,
        parent: tk.Misc,
        value: KeyCombo | None,
        *,
        width: int,
        background: str,
        name: Callable[[tuple[int | None, tuple[str, ...]]], str],
        empty: str,
        waiting: str,
        modifiers: Callable[[], tuple[str, ...]],
        on_change: Callable[[KeyCombo | None], None] | None = None,
    ) -> None:
        height = px(self.HEIGHT)
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=background,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=True,
        )
        self.value = value
        self._key_name, self._empty, self._waiting = name, empty, waiting
        self._modifiers_down = modifiers  # () -> names of the modifiers held now
        self._on_change = on_change
        self._prefix = ""  # the modifiers held while listening, e.g. "Ctrl+Shift+"
        self._listening = False
        self._error = False
        radius = px(self.RADIUS)
        self._imgs = {
            state: photo(
                self, outlined_pixels(width, height, radius, theme.SURFACE, border, background)
            )
            for state, border in (
                ("normal", theme.SURFACE_HI),
                ("listening", theme.ACCENT),
                ("error", theme.RED),
            )
        }
        self._box = self.create_image(0, 0, anchor="nw")
        self._text = self.create_text(
            px(self.PAD_X), height // 2, anchor="w", font=theme.FONT, fill=theme.TEXT
        )
        self._clear_x = width - px(self.CLEAR) // 2 - px(self.CLEAR_INSET)
        self._clear = self.create_text(
            self._clear_x, height // 2, text="✕", font=theme.FONT, fill=theme.SUBTEXT
        )
        self._draw()
        self.bind("<ButtonRelease-1>", self._click)
        self.bind("<KeyPress>", self._key)
        self.bind("<KeyRelease>", self._key_up)
        self.bind("<FocusOut>", lambda e: self._listen(False))

    def set_value(self, value: KeyCombo | None) -> None:
        self.value = value
        self._draw()

    def set_error(self, error: bool) -> None:
        self._error = error
        self._draw()

    def _draw(self) -> None:
        state = "listening" if self._listening else "error" if self._error else "normal"
        self.itemconfigure(self._box, image=self._imgs[state])
        if self._listening:
            text = self._prefix + "..." if self._prefix else self._waiting
            color = theme.ACCENT
        elif self.value is None:
            text, color = self._empty, theme.SUBTEXT
        else:
            text, color = self._key_name(self.value), theme.TEXT
        self.itemconfigure(self._text, text=text, fill=color)
        cleared = self.value is None or self._listening
        self.itemconfigure(self._clear, state="hidden" if cleared else "normal")

    def _listen(self, listening: bool) -> None:
        self._listening = listening
        self._prefix = ""
        if listening:
            self.focus_set()
        self._draw()

    def _click(self, e: tk.Event[tk.Canvas]) -> None:
        on_clear = e.x >= self._clear_x - px(self.CLEAR_SLACK)
        if self.value is not None and not self._listening and on_clear:
            self._set(None)
            return
        self._listen(True)

    def _key(self, e: tk.Event[tk.Canvas]) -> str | None:
        if not self._listening:
            return None
        if e.keysym in self.MODIFIER_KEYSYMS:
            self._show_prefix()
            return "break"
        self._listen(False)
        if e.keysym != "Escape":
            # Tk on Windows reports the virtual-key code as the keycode.
            self._set((e.keycode, self._modifiers_down()))
        return "break"  # keep the dialog's Enter and Escape out of it

    def _set(self, value: KeyCombo | None) -> None:
        self.set_value(value)
        if self._on_change is not None:
            self._on_change(value)

    def _key_up(self, e: tk.Event[tk.Canvas]) -> None:
        if self._listening and e.keysym in self.MODIFIER_KEYSYMS:
            self._show_prefix()

    def _show_prefix(self) -> None:
        held = self._modifiers_down()
        self._prefix = self._key_name((None, held)) if held else ""
        self._draw()


class ScrollList(tk.Frame):
    """A scrollable column: put children in `self.inner`.

    The thin scrollbar shows only when needed; the wheel scrolls anywhere over it.
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    BAR_WIDTH = 6
    GUTTER = 7
    MIN_THUMB = 24
    WHEEL_STEP = 24  # pixels per wheel notch
    MAX_CACHED_THUMBS = 32

    def __init__(self, parent: tk.Misc, *, width: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width
        self.view = tk.Canvas(
            self, width=width, bg=theme.BG, highlightthickness=0, bd=0, yscrollincrement=1
        )
        self.view.pack(side="left", fill="y")
        self.bar = tk.Canvas(
            self, width=px(self.BAR_WIDTH), bg=theme.BG, highlightthickness=0, bd=0
        )
        self.bar.pack(side="left", fill="y", padx=(px(self.GUTTER), 0))
        self.inner = tk.Frame(self.view, bg=theme.BG)
        self.view.create_window(0, 0, window=self.inner, anchor="nw", width=width)

        self._thumb = self.bar.create_image(0, 0, anchor="nw", state="hidden")
        self._thumb_images: dict[tuple[int, bool], tk.PhotoImage] = {}
        self._thumb_box: tuple[int, int] | None = None  # (top, height) while visible
        self._drag_offset: int | None = None
        self._hovered = False

        self.inner.bind("<Configure>", lambda e: self._content_changed())
        self.view.bind("<Configure>", lambda e: self._content_changed())
        self.view.configure(yscrollcommand=lambda first, last: self._draw_thumb())
        self.bar.bind("<ButtonPress-1>", self._press)
        self.bar.bind("<B1-Motion>", self._drag)
        self.bar.bind("<ButtonRelease-1>", self._release)
        self.bar.bind("<Enter>", lambda e: self._set_hovered(True))
        self.bar.bind("<Leave>", lambda e: self._set_hovered(False))
        # Every widget in the window carries the toplevel in its bindtags, so
        # this sees wheel events over the cards too; _wheel filters by position.
        self.winfo_toplevel().bind("<MouseWheel>", self._wheel, add="+")

    def _content_changed(self) -> None:
        self.view.configure(scrollregion=(0, 0, self._width, self.inner.winfo_reqheight()))
        if self.inner.winfo_reqheight() <= self.view.winfo_height():
            self.view.yview_moveto(0)
        self._draw_thumb()

    def _draw_thumb(self) -> None:
        first, last = self.view.yview()
        box = scroll_thumb(first, last, self.bar.winfo_height(), px(self.MIN_THUMB))
        self._thumb_box = box
        if box is None:
            self.bar.itemconfigure(self._thumb, state="hidden")
            return
        top, height = box
        active = self._hovered or self._drag_offset is not None
        self.bar.itemconfigure(self._thumb, image=self._thumb_image(height, active), state="normal")
        self.bar.coords(self._thumb, 0, top)

    def _thumb_image(self, height: int, active: bool) -> tk.PhotoImage:
        key = (height, active)
        if key not in self._thumb_images:
            if len(self._thumb_images) >= self.MAX_CACHED_THUMBS:
                self._thumb_images.clear()
            bar_width = px(self.BAR_WIDTH)
            style = ButtonStyle(
                fill=theme.SUBTEXT if active else theme.SURFACE_HI, radius=bar_width // 2
            )
            rows = button_pixels(bar_width, height, style, theme.BG)
            self._thumb_images[key] = photo(self.bar, rows)
        return self._thumb_images[key]

    def _set_hovered(self, hovered: bool) -> None:
        self._hovered = hovered
        self._draw_thumb()

    def _press(self, e: tk.Event[tk.Canvas]) -> None:
        if self._thumb_box is None:
            return
        top, height = self._thumb_box
        if top <= e.y < top + height:
            self._drag_offset = e.y - top
            self._draw_thumb()
        else:
            self.view.yview_scroll(-1 if e.y < top else 1, "pages")

    def _drag(self, e: tk.Event[tk.Canvas]) -> None:
        if self._drag_offset is None or self._thumb_box is None:
            return
        first, last = self.view.yview()
        self.view.yview_moveto(
            scroll_fraction(
                e.y - self._drag_offset,
                self._thumb_box[1],
                self.bar.winfo_height(),
                last - first,
            )
        )

    def _release(self, _event: tk.Event[tk.Canvas]) -> None:
        self._drag_offset = None
        self._draw_thumb()

    def _wheel(self, e: tk.Event[tk.Misc]) -> None:
        if self._thumb_box is None or not self._contains_pointer(e):
            return
        self.view.yview_scroll(round(-e.delta * px(self.WHEEL_STEP) / 120), "units")

    def _contains_pointer(self, e: tk.Event[tk.Misc]) -> bool:
        w = self.winfo_containing(e.x_root, e.y_root)
        while w is not None:
            if w is self:
                return True
            w = w.master
        return False


GLYPH_COPY = ""


class CopyText(tk.Canvas):
    """`text` with a copy icon; a click copies it and the hint says "Copied".

    With `max_width`, a long text is cut short with "…" but still copied in full.
    """

    # Where a tk.Label starts its text (2px border, 1px padding), to line up with one.
    # Tk doesn't scale those, so neither is this.
    INSET = 3
    # At 100% display scaling, scaled with px() where used.
    GAP = 6  # between the text and the icon
    SLACK = 2  # room above, below and after the glyphs, so the edges are easy to hit

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        *,
        background: str,
        fg: str | None = None,
        small: bool = False,
        inset: int = INSET,
        max_width: int | None = None,
    ) -> None:
        text_spec, icon_spec = (
            (theme.FONT_SMALL, theme.FONT_ICON_SMALL) if small else (theme.FONT, theme.FONT_ICON)
        )
        font = tkfont.Font(font=text_spec)
        icon_font = tkfont.Font(font=icon_spec)
        slack, gap = px(self.SLACK), px(self.GAP)
        icon_w = icon_font.measure(GLYPH_COPY)
        shown = text
        if max_width is not None:
            shown = elide(text, font, max_width - inset - gap - icon_w - slack)
        text_w = font.measure(shown)
        height = max(font.metrics("linespace"), icon_font.metrics("linespace")) + 2 * slack
        super().__init__(
            parent,
            width=inset + text_w + gap + icon_w + slack,
            height=height,
            bg=background,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._value = text
        self._fg = fg or theme.TEXT
        middle_y = height / 2
        self._text = self.create_text(inset, middle_y, text=shown, anchor="w", font=text_spec)
        self._icon = self.create_text(inset + text_w + gap, middle_y, anchor="w", font=icon_spec)
        self._tooltip = Tooltip(self.winfo_toplevel())
        self._hovered = self._pressed = self._copied = False
        self._paint()

        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Destroy>", lambda e: self._tooltip.hide())

    def _enter(self, _e: tk.Event[tk.Canvas]) -> None:
        self._hovered = True
        self._paint()
        self._tooltip.show(tr("Copy"), self._screen_box())

    def _leave(self, _e: tk.Event[tk.Canvas]) -> None:
        self._hovered = self._copied = False
        self._paint()
        self._tooltip.hide()

    def _press(self, _e: tk.Event[tk.Canvas]) -> None:
        self._pressed = True

    def _release(self, _e: tk.Event[tk.Canvas]) -> None:
        fire, self._pressed = self._pressed and self._hovered, False
        if not fire:
            return
        self.clipboard_clear()
        self.clipboard_append(self._value)
        self._copied = True
        self._paint()
        # Hidden first so the new hint opens at once, as when skimming between hints.
        self._tooltip.hide()
        self._tooltip.show(tr("Copied"), self._screen_box())

    def _screen_box(self) -> Box:
        x, y = self.winfo_rootx(), self.winfo_rooty()
        return x, y, x + self.winfo_width(), y + self.winfo_height()

    def _paint(self) -> None:
        self.itemconfigure(self._text, fill=theme.ACCENT if self._hovered else self._fg)
        if self._copied:
            self.itemconfigure(self._icon, text=GLYPH_CHECK, fill=theme.GREEN)
        else:
            fill = theme.ACCENT if self._hovered else theme.SUBTEXT
            self.itemconfigure(self._icon, text=GLYPH_COPY, fill=fill)
