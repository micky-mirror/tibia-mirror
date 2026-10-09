"""The Settings page: grouped cards of toggle, slider, choice and key rows."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from typing import TypedDict

from tibia_mirror.config import MIN_OPACITY, OPACITY_STEP
from tibia_mirror.core.settings import Settings
from tibia_mirror.core.timers import KeyCombo
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.animation import Tween
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.dialogs import key_combo_name
from tibia_mirror.ui.controls.slider import SliderDrawing
from tibia_mirror.ui.controls.widgets import KeyField, ScrollList, SegmentedDrawing
from tibia_mirror.winapi import win32

SWITCH_MS = 120


@dataclass(frozen=True)
class ToggleRow:
    key: str
    label: str
    value: bool
    hint: str = ""


@dataclass(frozen=True)
class SliderRow:
    key: str
    label: str
    value: float
    lo: float
    hi: float
    step: float
    format: Callable[[float], str]
    floor: float | None = None
    hint: str = ""


@dataclass(frozen=True)
class ChoiceRow:
    key: str
    label: str
    value: str
    options: tuple[tuple[str, str], ...]  # ((value, text), ...)
    hint: str = ""


@dataclass(frozen=True)
class KeyRow:
    key: str
    label: str
    value: KeyCombo | None
    hint: str = ""


Row = ToggleRow | SliderRow | ChoiceRow | KeyRow
# What a row's value can be; on_change(key, value) gets the row's own kind.
SettingValue = bool | float | str | KeyCombo | None
# on_change(key, value): None, or for a key row why the key was refused.
OnChange = Callable[[str, SettingValue], str | None]


class _Switch(TypedDict):
    """A toggle row's switch: its canvas items, where it is, and its running animation."""

    track: int
    knob: int
    x0: int
    middle_y: int
    tween: Tween | None


class SettingsGroup(tk.Canvas):
    """A rounded card of setting rows, drawn on one canvas like RegionCard.

    Toggle, slider, choice and key rows call on_change(key, value) at once. For a
    key row, on_change may return an error: the key is refused and the error shows
    in red instead of the row's help text.
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    PAD = 14
    RADIUS = 8
    ROW_PAD = 10  # above and below a row's content
    HINT_GAP = 2  # between a label and its help text
    SLIDER_GAP = 16  # from the help text to the slider's centre line
    SWITCH_GAP = 20  # between a toggle's text and its switch
    SWITCH_W, SWITCH_H = 36, 20
    SWITCH_KNOB = 12
    KEY_GAP = 8  # between a key row's help text and its field

    def __init__(
        self, parent: tk.Misc, rows: Sequence[Row], *, width: int, on_change: OnChange
    ) -> None:
        super().__init__(parent, width=width, height=1, bg=theme.BG, highlightthickness=0, bd=0)
        self._width = width
        self._row_list = rows
        # The current values, by row key, one dict per kind of row.
        self._flags = {row.key: row.value for row in rows if isinstance(row, ToggleRow)}
        self._numbers = {row.key: row.value for row in rows if isinstance(row, SliderRow)}
        self._choices = {row.key: row.value for row in rows if isinstance(row, ChoiceRow)}
        self._keys = {row.key: row.value for row in rows if isinstance(row, KeyRow)}
        self._errors: dict[str, str | None] = {}  # key row key -> shown instead of its hint
        self._on_change = on_change
        self._switch_imgs = self._render_switch_images()
        # Key fields are widgets on the canvas, kept across rebuilds.
        self._key_fields = {
            row.key: KeyField(
                self,
                row.value,
                width=width - 2 * px(self.PAD),
                background=theme.SURFACE,
                name=key_combo_name,
                empty=tr("Click to set a key"),
                waiting=tr("Press a key..."),
                modifiers=win32.modifiers_down,
                on_change=partial(self._key_changed, row),
            )
            for row in rows
            if isinstance(row, KeyRow)
        }
        self._rows: list[tuple[int, int, Row]] = []  # (y0, y1, row), top to bottom
        self._switches: dict[str, _Switch] = {}
        self._build()

        self.bind("<Enter>", self._motion)
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._release)

    # ---- construction -------------------------------------------------------
    def _build(self) -> None:
        """Draw every row from the current values; again whenever a row's height changes."""
        for switch in self._switches.values():
            if switch["tween"] is not None:
                switch["tween"].cancel()
        self.delete("all")
        self._readouts: dict[str, int] = {}  # slider row key -> readout text item
        self._switches = {}
        self._sliders: dict[str, SliderDrawing] = {}
        self._segments: dict[str, SegmentedDrawing] = {}
        self._hovered: Row | None = None
        self._pressed: Row | None = None
        self._dragging: SliderRow | None = None
        # (choice row, option) under the pointer, and where the button went down.
        self._hovered_option: tuple[ChoiceRow | None, str | None] | None = None
        self._pressed_option: tuple[ChoiceRow | None, str | None] | None = None
        self.configure(cursor="")
        card_item = self.create_image(0, 0, anchor="nw")  # first, so it stays at the bottom

        self._rows = []
        y = 0
        pad = px(self.PAD)
        for i, row in enumerate(self._row_list):
            if i:
                self.create_line(pad, y, self._width - pad, y, fill=theme.BG, width=px(1))
            if isinstance(row, ToggleRow):
                bottom = self._build_toggle(row, y)
            elif isinstance(row, SliderRow):
                bottom = self._build_slider(row, y)
            elif isinstance(row, ChoiceRow):
                bottom = self._build_choice(row, y)
            else:
                bottom = self._build_key(row, y)
            self._rows.append((y, bottom, row))
            y = bottom
        self.configure(height=y)
        card = ButtonStyle(fill=theme.SURFACE, radius=px(self.RADIUS))
        self._card_img = photo(self, button_pixels(self._width, y, card, theme.BG))
        self.itemconfigure(card_item, image=self._card_img)

    def _render_switch_images(
        self,
    ) -> tuple[dict[tuple[bool, bool], tk.PhotoImage], dict[tuple[bool, bool], tk.PhotoImage]]:
        """Track and knob images per (on, hovered); each knob is blended over its own track."""
        w, h, knob_size = px(self.SWITCH_W), px(self.SWITCH_H), px(self.SWITCH_KNOB)
        track_fill = {
            (False, False): theme.SURFACE_HI,
            (False, True): theme.OVERLAY,
            (True, False): theme.ACCENT,
            (True, True): theme.ACCENT_HI,
        }
        tracks, knobs = {}, {}
        for (is_on, hovered), fill in track_fill.items():
            tracks[is_on, hovered] = photo(
                self, button_pixels(w, h, ButtonStyle(fill=fill, radius=h // 2), theme.SURFACE)
            )
            knob = ButtonStyle(fill=theme.ON_ACCENT if is_on else theme.TEXT, radius=knob_size // 2)
            knobs[is_on, hovered] = photo(self, button_pixels(knob_size, knob_size, knob, fill))
        return tracks, knobs

    def _text_block(self, row: Row, y: int, hint_width: int) -> int:
        """The row's label with its help text wrapped under it; returns the text's bottom."""
        label = self.create_text(
            px(self.PAD),
            y + px(self.ROW_PAD),
            text=row.label,
            anchor="nw",
            font=theme.FONT,
            fill=theme.TEXT,
        )
        bottom = self.bbox(label)[3]
        error = self._errors.get(row.key)
        if row.hint or error:
            hint = self.create_text(
                px(self.PAD),
                bottom + px(self.HINT_GAP),
                text=error or row.hint,
                anchor="nw",
                width=hint_width,
                font=theme.FONT_SMALL,
                fill=theme.RED if error else theme.SUBTEXT,
            )
            bottom = self.bbox(hint)[3]
        return bottom

    def _build_toggle(self, row: ToggleRow, y: int) -> int:
        """Text on the left, the switch centred on the right; returns the row's bottom."""
        switch_w = px(self.SWITCH_W)
        hint_width = self._width - 2 * px(self.PAD) - switch_w - px(self.SWITCH_GAP)
        bottom = self._text_block(row, y, hint_width) + px(self.ROW_PAD)
        middle_y = (y + bottom) // 2
        x0 = self._width - px(self.PAD) - switch_w
        switch: _Switch = {
            "track": self.create_image(x0, middle_y - px(self.SWITCH_H) // 2, anchor="nw"),
            "knob": self.create_image(0, middle_y, anchor="w"),
            "x0": x0,
            "middle_y": middle_y,
            "tween": None,
        }
        self._switches[row.key] = switch
        self._draw_switch(row, switch, self._knob_x(switch, self._flags[row.key]))
        return bottom

    def _build_choice(self, row: ChoiceRow, y: int) -> int:
        """Text on the left, the options centred on the right; returns the row's bottom."""
        options_width = SegmentedDrawing.measure(row.options)
        hint_width = self._width - 2 * px(self.PAD) - options_width - px(self.SWITCH_GAP)
        bottom = self._text_block(row, y, hint_width) + px(self.ROW_PAD)
        choice = SegmentedDrawing(self, self._width - px(self.PAD), (y + bottom) // 2, row.options)
        choice.draw(self._choices[row.key], None)
        self._segments[row.key] = choice
        return bottom

    def _build_key(self, row: KeyRow, y: int) -> int:
        """Text, then the key field under it; returns the row's bottom."""
        pad = px(self.PAD)
        field_y = self._text_block(row, y, self._width - 2 * pad) + px(self.KEY_GAP)
        field = self._key_fields[row.key]
        self.create_window(pad, field_y, window=field, anchor="nw")
        return field_y + px(KeyField.HEIGHT) + px(self.ROW_PAD)

    def _build_slider(self, row: SliderRow, y: int) -> int:
        """Label and value readout, help text, then the slider; returns the row's bottom."""
        pad = px(self.PAD)
        readout = self.create_text(
            self._width - pad,
            y + px(self.ROW_PAD),
            anchor="ne",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )
        slider_y = self._text_block(row, y, self._width - 2 * pad) + px(self.SLIDER_GAP)
        slider = SliderDrawing(
            self,
            pad,
            self._width - pad,
            slider_y,
            self._numbers[row.key],
            lo=row.lo,
            hi=row.hi,
            step=row.step,
            floor=row.floor,
        )
        self._readouts[row.key] = readout
        self._sliders[row.key] = slider
        self.itemconfigure(readout, text=row.format(slider.value))
        return slider_y + px(SliderDrawing.KNOB) // 2 + px(self.ROW_PAD)

    # ---- drawing ------------------------------------------------------------
    def _knob_x(self, switch: _Switch, is_on: bool) -> int:
        knob, width = px(self.SWITCH_KNOB), px(self.SWITCH_W)
        inset = (px(self.SWITCH_H) - knob) // 2
        return switch["x0"] + (width - inset - knob if is_on else inset)

    def _draw_switch(self, row: ToggleRow, switch: _Switch, knob_x: float) -> None:
        is_on = self._flags[row.key]
        tracks, knobs = self._switch_imgs
        state = (is_on, row is self._hovered)
        self.itemconfigure(switch["track"], image=tracks[state])
        self.itemconfigure(switch["knob"], image=knobs[state])
        self.coords(switch["knob"], round(knob_x), switch["middle_y"])

    def _set_hovered(self, row: Row | None) -> None:
        if row is self._hovered:
            return
        previous, self._hovered = self._hovered, row
        for _top, _bottom, changed in self._rows:
            if changed in (previous, row):
                if isinstance(changed, ToggleRow):
                    switch = self._switches[changed.key]
                    self._draw_switch(
                        changed, switch, self._knob_x(switch, self._flags[changed.key])
                    )
                elif isinstance(changed, SliderRow) and self._dragging is not changed:
                    self._sliders[changed.key].set_active(changed is row)
        self.configure(cursor="hand2" if row else "")

    # ---- events -------------------------------------------------------------
    def _hit(self, e: tk.Event[tk.Misc]) -> Row | None:
        """The row reacting at the pointer: a toggle row, a slider's band, or an unchosen option."""
        for y0, y1, row in self._rows:
            if y0 <= e.y < y1:
                if isinstance(row, ToggleRow):
                    return row
                if isinstance(row, SliderRow) and self._sliders[row.key].contains(e.x, e.y):
                    return row
                if isinstance(row, ChoiceRow):
                    option = self._segments[row.key].at(e.x, e.y)
                    if option is not None and option != self._choices[row.key]:
                        return row
                return None
        return None

    def _option_at(self, e: tk.Event[tk.Misc]) -> tuple[ChoiceRow | None, str | None]:
        """(choice row, option) under the pointer, or (None, None)."""
        row = self._hit(e)
        if isinstance(row, ChoiceRow):
            return row, self._segments[row.key].at(e.x, e.y)
        return None, None

    def _leave(self, _e: tk.Event[tk.Misc]) -> None:
        self._set_hovered(None)
        self._set_hovered_option(None, None)

    def _motion(self, e: tk.Event[tk.Misc]) -> None:
        if self._dragging is None:
            self._set_hovered(self._hit(e))
            self._set_hovered_option(*self._option_at(e))

    def _set_hovered_option(self, row: ChoiceRow | None, option: str | None) -> None:
        if (row, option) == self._hovered_option:
            return
        previous, self._hovered_option = self._hovered_option, (row, option)
        for changed in {previous[0] if previous else None, row} - {None}:
            if changed is not None:
                hovered = option if changed is row else None
                self._segments[changed.key].draw(self._choices[changed.key], hovered)

    def _press(self, e: tk.Event[tk.Misc]) -> None:
        row = self._hit(e)
        self._pressed_option = self._option_at(e)
        if isinstance(row, SliderRow):
            self._dragging = row
            slider = self._sliders[row.key]
            slider.set_active(True)
            self._slide(row, slider, e.x)
        else:
            self._pressed = row

    def _drag(self, e: tk.Event[tk.Misc]) -> None:
        if self._dragging is not None:
            row = self._dragging
            self._slide(row, self._sliders[row.key], e.x)

    def _release(self, e: tk.Event[tk.Misc]) -> None:
        if self._dragging is not None:
            dragged, self._dragging = self._dragging, None
            self._set_hovered(None)
            self._set_hovered(self._hit(e))
            if dragged is not self._hovered:
                self._sliders[dragged.key].set_active(False)
            return
        row, self._pressed = self._pressed, None
        pressed_option, self._pressed_option = self._pressed_option, None
        if row is None or self._hit(e) is not row:
            return
        if isinstance(row, ChoiceRow):
            if pressed_option is not None and self._option_at(e) == pressed_option:
                option = pressed_option[1]
                if option is not None:
                    self._choose(row, option)
        elif isinstance(row, ToggleRow):
            self._toggle(row)

    def _choose(self, row: ChoiceRow, option: str) -> None:
        self._choices[row.key] = option
        self._segments[row.key].draw(option, None)
        self._set_hovered(None)
        self._on_change(row.key, option)

    def _slide(self, row: SliderRow, slider: SliderDrawing, x: int) -> None:
        value = slider.value_at(x)
        if value != slider.value:
            slider.set_value(value)
            self.itemconfigure(self._readouts[row.key], text=row.format(value))
            self._numbers[row.key] = value
            self._on_change(row.key, value)

    def _key_changed(self, row: KeyRow, value: KeyCombo | None) -> None:
        error = self._on_change(row.key, value)
        if error:
            self._key_fields[row.key].set_value(self._keys[row.key])
        else:
            self._keys[row.key] = value
        if error != self._errors.get(row.key):
            self._errors[row.key] = error
            self._build()

    def _toggle(self, row: ToggleRow) -> None:
        switch = self._switches[row.key]
        start = self._knob_x(switch, self._flags[row.key])
        self._flags[row.key] = not self._flags[row.key]
        end = self._knob_x(switch, self._flags[row.key])
        if switch["tween"] is not None:
            switch["tween"].cancel()
        switch["tween"] = Tween(
            self, start, end, SWITCH_MS, lambda x: self._draw_switch(row, switch, x)
        )
        self._on_change(row.key, self._flags[row.key])


def caption(parent: tk.Misc, text: str, first: bool = False) -> None:
    label = tk.Label(parent, text=text, bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT_CAPTION)
    label.pack(anchor="w", pady=(px(4 if first else 10), px(6)))


def build_groups_page(
    parent: tk.Misc,
    groups: Sequence[tuple[str, Sequence[Row]]],
    *,
    width: int,
    pad: int,
    on_change: OnChange,
) -> tk.Frame:
    """A page of captioned SettingsGroup cards, scrolling if needed: ((caption, rows), ...)."""
    page = tk.Frame(parent, bg=theme.BG)
    scroll = ScrollList(page, width=width)
    scroll.pack(anchor="w", fill="y", expand=True, padx=(pad, 0), pady=(px(14), px(8)))
    for i, (title, rows) in enumerate(groups):
        caption(scroll.inner, title, first=i == 0)
        SettingsGroup(scroll.inner, rows, width=width, on_change=on_change).pack(anchor="w")
    return page


def build_settings_page(
    parent: tk.Misc, settings: Settings, *, width: int, pad: int, on_change: OnChange
) -> tk.Frame:
    """The Settings page frame; every change calls on_change(key, value) right away."""
    groups: tuple[tuple[str, list[Row]], ...] = (
        (
            tr("GENERAL"),
            [
                # Language names are written in their own language, never translated.
                ChoiceRow(
                    "language",
                    tr("Language"),
                    settings.language,
                    (("en", "English"), ("pl", "Polski")),
                ),
                ChoiceRow(
                    "theme",
                    tr("Theme"),
                    settings.theme,
                    (("dark", tr("Dark")), ("light", tr("Light"))),
                ),
                ToggleRow(
                    "panel_on_top",
                    tr("Keep this panel on top"),
                    settings.panel_on_top,
                    tr("Stays above other windows."),
                ),
            ],
        ),
        (
            tr("PROFILES"),
            [
                ToggleRow(
                    "profile_per_character",
                    tr("Profile per character"),
                    settings.profile_per_character,
                    tr("Logging in opens the character's profile, creating one the first time."),
                ),
            ],
        ),
        (
            tr("SAVING"),
            [
                ToggleRow(
                    "autosave",
                    tr("Save automatically"),
                    settings.autosave,
                    tr("Saves every change as you make it."),
                ),
            ],
        ),
        (
            tr("MIRRORS"),
            [
                SliderRow(
                    "new_opacity",
                    tr("Opacity of new mirrors"),
                    settings.new_opacity,
                    0.0,
                    1.0,
                    OPACITY_STEP,
                    lambda value: f"{round(value * 100)}%",
                    floor=MIN_OPACITY,
                    hint=tr("Each mirror can still be set on its card."),
                ),
                ToggleRow(
                    "mirror_frame",
                    tr("Mirror frame"),
                    settings.mirror_frame,
                    tr("Grey outline on mirrors without a colour."),
                ),
                ToggleRow(
                    "frame_tint",
                    tr("Tint with frame colour"),
                    settings.frame_tint,
                    tr("Shades coloured mirrors in their colour."),
                ),
                ToggleRow(
                    "rounded_corners",
                    tr("Rounded corners"),
                    settings.rounded_corners,
                    tr("Clips a few pixels at each corner."),
                ),
                ToggleRow(
                    "fades",
                    tr("Fade animations"),
                    settings.fades,
                    tr("Off: mirrors appear and hide instantly."),
                ),
            ],
        ),
    )
    return build_groups_page(parent, groups, width=width, pad=pad, on_change=on_change)
