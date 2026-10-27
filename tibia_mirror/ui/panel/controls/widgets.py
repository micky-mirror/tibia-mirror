"""Custom Tk widgets, mostly drawn on a canvas for rounded, anti-aliased shapes."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.core.geometry import Box, scroll_fraction, scroll_thumb
from tibia_mirror.core.timers import KeyCombo
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels, margins, outlined_pixels
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.panel.controls.tooltip import Tip, Tooltip


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


# Segoe MDL2 Assets code points (FONT_ICON).
GLYPH_CHECK = "\ue73e"


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
        self._tooltip.show(Tip(tr("Copy")), self._screen_box())

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
        self._tooltip.show(Tip(tr("Copied")), self._screen_box())

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
