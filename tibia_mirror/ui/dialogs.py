"""Modal popups: names, choices, a region's position and size, timers, characters, copy-from."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from functools import partial

from tibia_mirror.config import MAX_NAME_LENGTH, TIMER_SOUNDS
from tibia_mirror.core import characters
from tibia_mirror.core.characters import Links
from tibia_mirror.core.geometry import Point, Rect, region_error
from tibia_mirror.core.timers import KeyCombo, TimerSettings, combo_name, key_clashes, parse_alert
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import margins, outlined_pixels
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.menu import DropdownField
from tibia_mirror.ui.widgets import (
    CheckBox,
    ChoiceBar,
    KeyField,
    RaisedButton,
    SegmentedDrawing,
    TextField,
)
from tibia_mirror.winapi import dwm, sounds, win32

# Sizes at 100% display scaling, scaled with px() where used.
WIDTH = 340
PAD = 18
BUTTON_GAP = 12
BUTTON_HEIGHT = 34
BUTTONS_GAP_ABOVE = 16  # between the content and the button row
# The popup's border, 1px on each side: Windows draws it (or _Popup does, on
# Windows 10), and it stays 1px at any scaling.
BORDER = 2

# config.TIMER_SOUNDS names -> their labels (English; translated when shown).
SOUND_LABELS = {
    "asterisk": "Asterisk",
    "exclamation": "Exclamation",
    "notification": "Notification",
    "critical": "Critical stop",
    "beep": "Beep",
    "none": "No sound",
}


@dataclass(frozen=True)
class Choice:
    label: str
    command: Callable[[], None]
    kind: str = "secondary"  # "secondary", "primary" or "danger"


def button_colors(kind: str) -> tuple[str, str, str]:
    """(fill, hover fill, text colour) for a Choice.kind, in the current theme."""
    return {
        "secondary": (theme.SURFACE, theme.SURFACE_HI, theme.TEXT),
        "primary": (theme.ACCENT, theme.ACCENT_HI, theme.ON_ACCENT),
        "danger": (theme.RED, theme.RED_HI, theme.ON_ACCENT),
    }[kind]


def fit_name(template: str, name: str, font: tkfont.Font, max_width: int) -> str:
    """`template` with {name} filled in, the name cut short with "…" to fit max_width."""
    if font.measure(template.format(name=name)) <= max_width:
        return template.format(name=name)
    shown = name
    while shown and font.measure(template.format(name=shown + "…")) > max_width:
        shown = shown[:-1]
    return template.format(name=shown + "…")


class _Popup:
    """Borderless, topmost, modal popup centred on `center`, kept on its monitor.

    Subclasses fill `self.body` above the button row, then call _open(). Escape
    runs the popup's cancel action.
    """

    def __init__(
        self, root: tk.Misc, title: str, width: int | None = None, name: str | None = None
    ) -> None:
        """`width` is in pixels at the current scaling; by default, WIDTH scaled.

        With `name`, `title` is a translated template with a {name} field, e.g.
        'Timer for "{name}"'; a name too long for one line is cut short with "…".
        """
        self.width = px(WIDTH) if width is None else width
        self.inner_width = self.width - BORDER - 2 * px(PAD)
        self.win = tk.Toplevel(root, bg=theme.SURFACE_HI)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        # On Windows 10 a 1px SURFACE_HI frame shows around the body; on 11,
        # Windows draws the border itself, with rounded corners (see _open).
        self.body = tk.Frame(self.win, bg=theme.BG)
        self.body.pack(fill="both", expand=True, padx=dwm.POPUP_FRAME, pady=dwm.POPUP_FRAME)
        font = tkfont.Font(font=theme.FONT_BOLD)
        if name is not None:
            title = fit_name(title, name, font, self.inner_width)
        tk.Label(self.body, text=title, bg=theme.BG, fg=theme.TEXT, font=font).pack(
            anchor="w", padx=px(PAD), pady=(px(PAD), px(8))
        )
        self._title_font = font  # Tk fonts must outlive their widgets
        self._center: Point | None = None  # set by _open

    def _button_row(self, choices: Sequence[Choice]) -> tk.Frame:
        """Equal-width buttons across the popup, the last (primary) one on the right."""
        row = tk.Frame(self.body, bg=theme.BG)
        # Tk can't overlap the canvases, so each gap holds both shadow margins at least.
        shadow = margins(theme.SECONDARY_BUTTON)
        gap = max(px(BUTTON_GAP), shadow.left + shadow.right)
        width = (self.inner_width - gap * (len(choices) - 1)) // len(choices)
        buttons = []
        for choice in choices:
            fill, hover, fg = button_colors(choice.kind)
            buttons.append(
                RaisedButton(
                    row,
                    choice.label,
                    choice.command,
                    width=width,
                    height=px(BUTTON_HEIGHT),
                    style=replace(theme.SECONDARY_BUTTON, fill=fill),
                    hover_fill=hover,
                    font=theme.FONT_BOLD,
                    fg=fg,
                    background=theme.BG,
                )
            )
        pad = px(PAD)
        row.pack(
            anchor="w",
            padx=(pad - shadow.left, 0),
            pady=(px(BUTTONS_GAP_ABOVE) - shadow.top, pad - shadow.bottom),
        )
        for i, button in enumerate(buttons):
            button.pack(side="left", padx=(0 if i == 0 else gap - shadow.right - shadow.left, 0))
        return row

    def _open(self, center: Point, on_escape: Callable[[], None]) -> None:
        self._center = center
        self.win.bind("<Escape>", lambda e: on_escape())
        # Alt+F4 while it is active: the same as Escape, never a bare destroy.
        self.win.protocol("WM_DELETE_WINDOW", on_escape)
        self._place()
        self.win.deiconify()
        dwm.round_popup(win32.toplevel_hwnd(self.win), theme.SURFACE_HI)
        self.win.grab_set()
        self.win.focus_force()

    def _place(self) -> None:
        """Size to content and centre on the anchor; call again when the content grows."""
        if self._center is None:
            return  # not open yet: _open places it
        center_x, center_y = self._center
        self.win.update_idletasks()
        w, h = self.width, self.win.winfo_reqheight()
        area = win32.work_area_at(self._center)
        x = min(max(center_x - w // 2, area.x), area.right - w)
        y = min(max(center_y - h // 2, area.y), area.bottom - h)
        self.win.geometry(f"{w}x{h}+{x}+{y}")

    def _close(self) -> None:
        self.win.grab_release()
        self.win.destroy()


class NameDialog(_Popup):
    """Asks for a name, starting with `default_name` selected.

    OK or Enter calls on_ok(name) (blank means the default); Cancel or Escape calls
    on_cancel(). `validate(name)` returns an error to show, or None.
    """

    def __init__(
        self,
        root: tk.Misc,
        default_name: str,
        center: Point,
        on_ok: Callable[[str], None],
        on_cancel: Callable[[], None],
        title: str | None = None,
        validate: Callable[[str], str | None] | None = None,
    ) -> None:
        super().__init__(root, title or tr("Name this region"))
        self._default = default_name
        self._on_ok, self._on_cancel = on_ok, on_cancel
        self._validate = validate

        self.name = tk.StringVar(value=default_name)
        self.name.trace_add("write", self._edited)
        self.field = TextField(self.body, self.name, width=self.inner_width, background=theme.BG)
        self.field.pack(anchor="w", padx=px(PAD))
        self.entry = self.field.entry
        # Packed only while there is an error, so the dialog is compact otherwise.
        self.error = tk.Label(
            self.body,
            bg=theme.BG,
            fg=theme.RED,
            font=theme.FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=self.inner_width,
        )
        self._error_shown = False
        self._buttons = self._button_row(
            [Choice(tr("Cancel"), self._cancel), Choice(tr("OK"), self._ok, "primary")]
        )

        self.win.bind("<Return>", lambda e: self._ok())
        self.win.bind("<KP_Enter>", lambda e: self._ok())
        self._open(center, self._cancel)
        self.entry.focus_set()
        self.entry.select_range(0, "end")
        self.entry.icursor("end")

    def _edited(self, *_: object) -> None:
        value = self.name.get()
        if len(value) > MAX_NAME_LENGTH:
            self.name.set(value[:MAX_NAME_LENGTH])
        self._show_error(None)

    def _show_error(self, text: str | None) -> None:
        if not text and not self._error_shown:
            return
        if text:
            self.error.config(text=text)
            if not self._error_shown:
                self.error.pack(before=self._buttons, fill="x", padx=px(PAD), pady=(px(6), 0))
        else:
            self.error.pack_forget()
        self.field.set_error(bool(text))
        self._error_shown = bool(text)
        self._place()

    def _ok(self) -> None:
        name = self.name.get().strip() or self._default
        error = self._validate(name) if self._validate else None
        if error:
            self._show_error(tr(error))
            self.entry.focus_set()
            return
        self._close()
        self._on_ok(name)

    def _cancel(self) -> None:
        self._close()
        self._on_cancel()


class ChoiceDialog(_Popup):
    """A message and a row of buttons; each closes the dialog, then runs its command.

    Enter picks the primary choice, never a danger one, so a stray Enter deletes nothing.
    """

    def __init__(
        self,
        root: tk.Misc,
        title: str,
        message: str,
        center: Point,
        choices: Sequence[Choice],
        on_cancel: Callable[[], None] = lambda: None,
    ) -> None:
        super().__init__(root, title)
        tk.Label(
            self.body,
            text=message,
            bg=theme.BG,
            fg=theme.TEXT,
            font=theme.FONT,
            anchor="w",
            justify="left",
            wraplength=self.inner_width,
        ).pack(fill="x", padx=px(PAD))
        self._button_row(
            [replace(choice, command=self._closing(choice.command)) for choice in choices]
        )
        primary = next((choice for choice in choices if choice.kind == "primary"), None)
        if primary is not None:
            self.win.bind("<Return>", lambda e: self._closing(primary.command)())
        self._open(center, self._closing(on_cancel))

    def _closing(self, command: Callable[[], None]) -> Callable[[], None]:
        def run() -> None:
            self._close()
            command()

        return run


class RegionDialog(_Popup):
    """A mirror region's position, size and zoom, previewed live on the mirror.

    Values are game pixels (zoom in percent); Up/Down change a field by 1, Shift by 10.
    Calls on_preview(rect, zoom) on each valid edit and on_ok(rect, zoom, apply_to_all)
    on OK; "Select area again" calls on_reselect().
    """

    FIELD_GAP = 28  # room for the "×" between paired fields
    FIELDS = (("x", "X"), ("y", "Y"), ("w", "Width"), ("h", "Height"), ("zoom", "Zoom %"))

    def __init__(
        self,
        root: tk.Misc,
        name: str,
        rect: Rect,
        zoom: float,
        client_size: tuple[int, int],
        minimum: int,
        zoom_range: tuple[float, float],
        center: Point,
        *,
        on_preview: Callable[[Rect, float], None],
        on_ok: Callable[[Rect, float, bool], None],
        on_reselect: Callable[[], None],
        on_cancel: Callable[[], None],
        can_apply_to_all: bool,
    ) -> None:
        super().__init__(root, tr('Region "{name}"'), name=name)
        self._client_size, self._minimum = client_size, minimum
        self._zoom_pct = (round(zoom_range[0] * 100), round(zoom_range[1] * 100))
        self._on_preview, self._on_ok = on_preview, on_ok
        self._on_reselect, self._on_cancel = on_reselect, on_cancel

        field_gap = px(self.FIELD_GAP)
        field_width = (self.inner_width - field_gap) // 2
        grid = tk.Frame(self.body, bg=theme.BG)
        grid.pack(anchor="w", padx=px(PAD))
        grid.grid_columnconfigure(1, minsize=field_gap)
        digits = (
            self.win.register(
                lambda proposed: proposed == "" or (proposed.isdigit() and len(proposed) <= 4)
            ),
            "%P",
        )
        start = {"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h, "zoom": round(zoom * 100)}
        self._vars: dict[str, tk.StringVar] = {}
        self._fields: dict[str, TextField] = {}
        for i, (key, label) in enumerate(self.FIELDS):
            row, column = (i // 2) * 2, (i % 2) * 2
            tk.Label(
                grid, text=tr(label), bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT_SMALL
            ).grid(row=row, column=column, sticky="w", pady=(0 if row == 0 else px(10), px(4)))
            text_var = tk.StringVar(value=str(start[key]))
            field = TextField(grid, text_var, width=field_width, background=theme.BG)
            field.entry.configure(validate="key", validatecommand=digits)
            field.grid(row=row + 1, column=column)
            for sequence, step in (
                ("<Up>", 1),
                ("<Down>", -1),
                ("<Shift-Up>", 10),
                ("<Shift-Down>", -10),
            ):
                field.entry.bind(sequence, partial(self._step, key, step))
            text_var.trace_add("write", partial(self._edited, key))
            self._vars[key], self._fields[key] = text_var, field
        tk.Label(grid, text="×", bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT).grid(
            row=3, column=1
        )
        tk.Label(
            self.body,
            text=tr("Game pixels. Up/Down change a value by 1, Shift by 10."),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
            wraplength=self.inner_width,
            justify="left",
        ).pack(anchor="w", padx=px(PAD), pady=(px(8), 0))

        self._apply_all: CheckBox | None = None
        if can_apply_to_all:
            self._apply_all = CheckBox(
                self.body,
                tr("Apply size and zoom to all mirrors"),
                background=theme.BG,
                width=self.inner_width,
            )
            self._apply_all.pack(anchor="w", padx=px(PAD), pady=(px(12), 0))

        link_font, underlined = tkfont.Font(font=theme.FONT), tkfont.Font(font=theme.FONT)
        underlined.configure(underline=True)
        self._fonts = (link_font, underlined)  # Tk fonts must outlive the label
        link = tk.Label(
            self.body,
            text=tr("Select area again"),
            bg=theme.BG,
            fg=theme.ACCENT,
            font=link_font,
            cursor="hand2",
        )
        link.pack(anchor="w", padx=px(PAD), pady=(px(12), 0))
        link.bind("<Enter>", lambda e: link.configure(font=underlined, fg=theme.ACCENT_HI))
        link.bind("<Leave>", lambda e: link.configure(font=link_font, fg=theme.ACCENT))
        link.bind("<ButtonRelease-1>", lambda e: self._reselect())

        self.error = tk.Label(
            self.body,
            bg=theme.BG,
            fg=theme.RED,
            font=theme.FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=self.inner_width,
        )
        self._error_shown = False
        self._buttons = self._button_row(
            [Choice(tr("Cancel"), self._cancel), Choice(tr("OK"), self._ok, "primary")]
        )
        self.win.bind("<Return>", lambda e: self._ok())
        self.win.bind("<KP_Enter>", lambda e: self._ok())
        self._open(center, self._cancel)
        entry = self._fields["w"].entry
        entry.focus_set()
        entry.select_range(0, "end")
        entry.icursor("end")

    # ---- values -------------------------------------------------------------
    def _values(self) -> dict[str, int] | None:
        """The fields as numbers, or None while one is empty."""
        texts = {key: text_var.get() for key, text_var in self._vars.items()}
        return None if "" in texts.values() else {key: int(text) for key, text in texts.items()}

    def _problem(self, values: dict[str, int]) -> tuple[str, dict[str, int], str] | None:
        """(message, values, field) for the first value that does not fit, or None."""
        client_w, client_h = self._client_size
        problem = region_error(
            values["x"], values["y"], values["w"], values["h"], client_w, client_h, self._minimum
        )
        if problem:
            return problem
        lo, hi = self._zoom_pct
        if not lo <= values["zoom"] <= hi:
            return "Zoom must be {lo} to {hi}%", {"lo": lo, "hi": hi}, "zoom"
        return None

    @staticmethod
    def _result(values: dict[str, int]) -> tuple[Rect, float]:
        rect = Rect(values["x"], values["y"], values["w"], values["h"])
        return rect, values["zoom"] / 100

    def _step(self, key: str, delta: int, _e: tk.Event[tk.Misc]) -> str:
        value = self._values()
        if value is not None:
            client_w, client_h = self._client_size
            lo, hi = {
                "x": (0, client_w - value["w"]),
                "y": (0, client_h - value["h"]),
                "w": (self._minimum, client_w - value["x"]),
                "h": (self._minimum, client_h - value["y"]),
                "zoom": self._zoom_pct,
            }[key]
            self._vars[key].set(str(min(hi, max(lo, value[key] + delta))))
        return "break"  # keep Up/Down from doing anything else

    def _edited(self, key: str, *_: object) -> None:
        self._fields[key].set_error(False)
        self._show_error(None)
        values = self._values()
        if values is not None and self._problem(values) is None:
            self._on_preview(*self._result(values))

    # ---- buttons ------------------------------------------------------------
    def _show_error(self, text: str | None) -> None:
        if not text and not self._error_shown:
            return
        if text:
            self.error.config(text=text)
            if not self._error_shown:
                self.error.pack(before=self._buttons, fill="x", padx=px(PAD), pady=(px(8), 0))
        else:
            self.error.pack_forget()
        self._error_shown = bool(text)
        self._place()

    def _ok(self) -> None:
        values = self._values()
        if values is None:
            self._reject(
                tr("Fill in every value"),
                next(key for key, text_var in self._vars.items() if not text_var.get()),
            )
            return
        problem = self._problem(values)
        if problem:
            message, fields, key = problem
            self._reject(tr(message, **fields), key)
            return
        apply_to_all = self._apply_all is not None and self._apply_all.value
        self._close()
        self._on_ok(*self._result(values), apply_to_all)

    def _reject(self, text: str, key: str) -> None:
        """Show why OK did not go through, on the field to fix."""
        self._show_error(text)
        self._fields[key].set_error(True)
        self._fields[key].entry.focus_set()

    def _reselect(self) -> None:
        self._close()
        self._on_reselect()

    def _cancel(self) -> None:
        self._close()
        self._on_cancel()


def key_combo_name(value: tuple[int | None, tuple[str, ...]]) -> str:
    """A KeyField value, (virtual-key code or None, modifiers), written out: "Shift+F9"."""
    vk, modifiers = value
    return combo_name(modifiers, "" if vk is None else win32.key_name(vk))


class TimerDialog(_Popup):
    """A mirror's timer: on/off, alert time, direction, trigger, sound, logout pause.

    OK calls on_ok(TimerSettings) once the time is valid and the key isn't
    `reserved` (the hide-all key). Choosing a sound plays it.
    """

    LABEL_GAP = 16  # between the labels and the controls
    MIN_CONTROL = 200  # the key and sound fields are at least this wide

    def __init__(
        self,
        root: tk.Misc,
        name: str,
        settings: TimerSettings,
        center: Point,
        on_ok: Callable[[TimerSettings], None],
        on_cancel: Callable[[], None],
        reserved: KeyCombo | None = None,
    ) -> None:
        # Sized to fit the longest label and option bar in the current language.
        labels = [tr(label) for label in ("Alert after", "Count", "Mouse button", "Key", "Sound")]
        directions = (("down", tr("Down")), ("up", tr("Up")))
        buttons = (("left", tr("Left")), ("right", tr("Right")), ("both", tr("Both")))
        font = tkfont.Font(font=theme.FONT)
        label_width = max(font.measure(label) for label in labels) + px(self.LABEL_GAP)
        control_width = max(
            px(self.MIN_CONTROL),
            SegmentedDrawing.measure(directions),
            SegmentedDrawing.measure(buttons),
        )
        width = max(px(WIDTH), BORDER + 2 * px(PAD) + label_width + control_width)
        super().__init__(root, tr('Timer for "{name}"'), width=width, name=name)
        control_width = self.inner_width - label_width
        self._on_ok, self._on_cancel = on_ok, on_cancel
        self._reserved = reserved
        self._error_shown = False

        self._enabled = CheckBox(
            self.body,
            tr("Timer on"),
            value=settings.enabled,
            background=theme.BG,
            width=self.inner_width,
        )
        self._enabled.pack(anchor="w", padx=px(PAD), pady=(0, px(10)))

        grid = tk.Frame(self.body, bg=theme.BG)
        grid.pack(anchor="w", padx=px(PAD))
        grid.grid_columnconfigure(0, minsize=label_width)

        def row(index: int, label: str, widget: tk.Widget) -> None:
            tk.Label(grid, text=label, bg=theme.BG, fg=theme.TEXT, font=theme.FONT, bd=0).grid(
                row=index, column=0, sticky="w", pady=px(4)
            )
            widget.grid(row=index, column=1, sticky="w", pady=px(4))

        alert = tk.Frame(grid, bg=theme.BG)
        digits = (
            self.win.register(
                lambda proposed: proposed == "" or (proposed.isdigit() and len(proposed) <= 2)
            ),
            "%P",
        )
        minutes, seconds = divmod(settings.alert, 60)
        self._minutes = tk.StringVar(value=str(minutes))
        self._seconds = tk.StringVar(value=f"{seconds:02d}")
        self._fields: list[TextField] = []
        units = ((self._minutes, tr("min")), (self._seconds, tr("s")))
        # The two fields share what the unit labels leave, so the row ends where the others do.
        unit_gap, field_gap = px(6), px(12)
        unit_widths = sum(font.measure(unit) for _, unit in units)
        field_width = (control_width - unit_widths - 2 * unit_gap - field_gap) // 2
        for i, (text_var, unit) in enumerate(units):
            field = TextField(alert, text_var, width=field_width, background=theme.BG)
            field.entry.configure(validate="key", validatecommand=digits)
            field.pack(side="left", padx=(0 if i == 0 else field_gap, 0))
            tk.Label(
                alert, text=unit, bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT, bd=0, padx=0
            ).pack(side="left", padx=(unit_gap, 0))
            text_var.trace_add("write", partial(self._edited, field))
            self._fields.append(field)
        row(0, tr("Alert after"), alert)

        # Every control in the column is the same width and height, like the fields.
        def bar(options: Sequence[tuple[str, str]], value: str) -> ChoiceBar:
            return ChoiceBar(
                grid,
                options,
                value,
                background=theme.BG,
                width=control_width,
                height=px(TextField.HEIGHT),
            )

        self._direction = bar(directions, settings.direction)
        row(1, tr("Count"), self._direction)
        self._button = bar(buttons, settings.button)
        row(2, tr("Mouse button"), self._button)
        self._key = KeyField(
            grid,
            settings.combo,
            width=control_width,
            background=theme.BG,
            name=key_combo_name,
            empty=tr("Click to set a key"),
            waiting=tr("Press a key..."),
            modifiers=win32.modifiers_down,
            on_change=lambda _value: self._edited(self._key),
        )
        row(3, tr("Key"), self._key)
        self._sound = DropdownField(
            grid,
            [(name, tr(SOUND_LABELS[name])) for name in TIMER_SOUNDS],
            settings.sound,
            width=control_width,
            background=theme.BG,
            on_pick=sounds.play,
        )
        row(4, tr("Sound"), self._sound)

        self._offline_pause = CheckBox(
            self.body,
            tr("Pause while logged out"),
            value=settings.offline_pause,
            background=theme.BG,
            width=self.inner_width,
        )
        self._offline_pause.pack(anchor="w", padx=px(PAD), pady=(px(10), 0))
        tk.Label(
            self.body,
            text=tr(
                "For timers that only count while your character is online: "
                "each character continues from where it logged out."
            ),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
            wraplength=self.inner_width,
            justify="left",
        ).pack(anchor="w", padx=px(PAD), pady=(px(2), 0))
        tk.Label(
            self.body,
            text=tr("A click on this region in the game, or the key, starts it again."),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
            wraplength=self.inner_width,
            justify="left",
        ).pack(anchor="w", padx=px(PAD), pady=(px(8), 0))
        self.error = tk.Label(
            self.body,
            bg=theme.BG,
            fg=theme.RED,
            font=theme.FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=self.inner_width,
        )
        self._buttons = self._button_row(
            [Choice(tr("Cancel"), self._cancel), Choice(tr("OK"), self._ok, "primary")]
        )
        self.win.bind("<Return>", lambda e: self._ok())
        self.win.bind("<KP_Enter>", lambda e: self._ok())
        self._open(center, self._cancel)
        if reserved is not None and key_clashes(settings, reserved):
            self._key_taken(reserved)

    def _edited(self, field: TextField | KeyField, *_: object) -> None:
        field.set_error(False)
        if self._error_shown:
            self.error.pack_forget()
            self._error_shown = False
            self._place()

    def _show_error(self, text: str, fields: Sequence[TextField | KeyField]) -> None:
        self.error.config(text=text)
        if not self._error_shown:
            self.error.pack(before=self._buttons, fill="x", padx=px(PAD), pady=(px(8), 0))
            self._error_shown = True
            self._place()
        for field in fields:
            field.set_error(True)

    def _key_taken(self, reserved: KeyCombo) -> None:
        self._show_error(
            tr(
                "{key} hides all mirrors (see Shortcuts). Pick another key.",
                key=key_combo_name(reserved),
            ),
            [self._key],
        )

    def _ok(self) -> None:
        alert = parse_alert(self._minutes.get(), self._seconds.get())
        if alert is None:
            self._show_error(tr("The alert time must be 0:01 to 59:59."), self._fields)
            return
        key, modifiers = self._key.value or (None, ())
        settings = TimerSettings(
            enabled=self._enabled.value,
            alert=alert,
            direction=self._direction.value,
            button=self._button.value,
            key=key,
            modifiers=modifiers,
            sound=self._sound.value,
            offline_pause=self._offline_pause.value,
        )
        if self._reserved is not None and key_clashes(settings, self._reserved):
            self._key_taken(self._reserved)
            return
        self._close()
        self._on_ok(settings)

    def _cancel(self) -> None:
        self._close()
        self._on_cancel()


class _ListRow(tk.Canvas):
    """A rounded row showing `text`, with a ✕ on the right that calls on_remove()."""

    # Sizes at 100% display scaling, scaled with px() where used.
    HEIGHT = 32
    PAD_X = 10
    RADIUS = 8
    REMOVE = 28  # the ✕'s clickable width

    def __init__(
        self, parent: tk.Misc, text: str, *, width: int, on_remove: Callable[[], None]
    ) -> None:
        self._height = height = px(self.HEIGHT)
        super().__init__(
            parent, width=width, height=height, bg=theme.BG, highlightthickness=0, bd=0
        )
        self._on_remove = on_remove
        box = outlined_pixels(
            width, height, px(self.RADIUS), theme.SURFACE, theme.SURFACE_HI, theme.BG
        )
        self._img = photo(self, box)
        self.create_image(0, 0, anchor="nw", image=self._img)
        middle_y = height // 2
        self.create_text(
            px(self.PAD_X), middle_y, text=text, anchor="w", font=theme.FONT, fill=theme.TEXT
        )
        remove = px(self.REMOVE)
        self._remove_x = width - remove
        self._remove_mark = self.create_text(
            width - remove // 2, middle_y, text="✕", font=theme.FONT, fill=theme.SUBTEXT
        )
        self._on_x = False
        self.bind("<Motion>", lambda e: self._hover(e.x >= self._remove_x))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<ButtonRelease-1>", self._release)

    def _hover(self, on_x: bool) -> None:
        if on_x != self._on_x:
            self._on_x = on_x
            self.itemconfigure(self._remove_mark, fill=theme.RED if on_x else theme.SUBTEXT)
            self.configure(cursor="hand2" if on_x else "")

    def _release(self, e: tk.Event[tk.Canvas]) -> None:
        if e.x >= self._remove_x and 0 <= e.y < self._height:
            self._on_remove()


class CharactersDialog(_Popup):
    """The characters whose login opens `profile`: remove from the list, or add a name.

    Each change calls on_change(links) with all links. A name linked elsewhere says
    so while typed, and adding it moves it here.
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    ADD_WIDTH = 84
    ROW_GAP = 6

    def __init__(
        self,
        root: tk.Misc,
        profile: str,
        links: Links,
        center: Point,
        on_change: Callable[[Links], None],
    ) -> None:
        super().__init__(root, tr('Characters of "{name}"'), name=profile)
        self._profile, self._links, self._on_change = profile, links, on_change

        tk.Label(
            self.body,
            text=tr(
                "Logging in with one of these characters opens this profile, "
                "while Profile per character is on in Settings."
            ),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=self.inner_width,
        ).pack(fill="x", padx=px(PAD), pady=(0, px(10)))
        self._list = tk.Frame(self.body, bg=theme.BG)
        self._list.pack(anchor="w", padx=px(PAD))

        add_row = tk.Frame(self.body, bg=theme.BG)
        add_row.pack(anchor="w", padx=px(PAD), pady=(px(10), 0))
        self.name = tk.StringVar()
        self.name.trace_add("write", self._edited)
        self.field = TextField(
            add_row,
            self.name,
            width=self.inner_width - px(BUTTON_GAP) - px(self.ADD_WIDTH),
            background=theme.BG,
        )
        self.field.pack(side="left")
        add = RaisedButton(
            add_row,
            tr("Add"),
            self._add,
            width=px(self.ADD_WIDTH),
            height=px(TextField.HEIGHT),
            style=theme.SECONDARY_BUTTON,
            hover_fill=theme.SURFACE_HI,
            font=theme.FONT_BOLD,
            fg=theme.TEXT,
            background=theme.BG,
        )
        shadow = add.margins
        # The button's shadow margins overlap the gap, so its body lines up with the field.
        add_row.pack_configure(pady=(px(10) - shadow.top, 0))
        self.field.pack_configure(pady=(shadow.top, shadow.bottom))
        add.pack(side="left", padx=(px(BUTTON_GAP) - shadow.left, 0))
        self.note = tk.Label(
            self.body,
            bg=theme.BG,
            font=theme.FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=self.inner_width,
        )
        self._note_shown = False
        self._buttons = self._button_row([Choice(tr("Done"), self._done, "primary")])
        self._fill_list()

        self.field.entry.bind("<Return>", lambda e: self._enter())
        self.field.entry.bind("<KP_Enter>", lambda e: self._enter())
        self._open(center, self._done)
        self.field.entry.focus_set()

    def _fill_list(self) -> None:
        for child in self._list.winfo_children():
            child.destroy()
        names = characters.characters_of(self._links, self._profile)
        if not names:
            tk.Label(
                self._list,
                text=tr("No characters yet."),
                bg=theme.BG,
                fg=theme.SUBTEXT,
                font=theme.FONT,
            ).pack(anchor="w")
        for i, name in enumerate(names):
            _ListRow(
                self._list, name, width=self.inner_width, on_remove=partial(self._remove, name)
            ).pack(anchor="w", pady=(0 if i == 0 else px(self.ROW_GAP), 0))
        self._place()

    def _entered(self) -> str:
        return " ".join(self.name.get().split())

    def _edited(self, *_: object) -> None:
        value = self.name.get()
        if len(value) > MAX_NAME_LENGTH:
            self.name.set(value[:MAX_NAME_LENGTH])
            return
        self.field.set_error(False)
        name = self._entered()
        other = characters.profile_of(self._links, name) if name else None
        if other is not None and other.casefold() != self._profile.casefold():
            self._show_note(tr('Linked to "{profile}" - adding moves it here.', profile=other))
        else:
            self._show_note(None)

    def _show_note(self, text: str | None, error: bool = False) -> None:
        if text:
            self.note.config(text=text, fg=theme.RED if error else theme.YELLOW)
            if not self._note_shown:
                self.note.pack(before=self._buttons, fill="x", padx=px(PAD), pady=(px(6), 0))
                self._note_shown = True
        elif self._note_shown:
            self.note.pack_forget()
            self._note_shown = False
        self._place()

    def _enter(self) -> None:
        if self._entered():
            self._add()
        else:
            self._done()

    def _add(self) -> None:
        name = self._entered()
        error = characters.character_error(name)
        if error:
            self.field.set_error(True)
            self._show_note(tr(error), error=True)
            return
        # A name linked before keeps its spelling: from the game's title, it is exact.
        name = characters.spelling(self._links, name)
        self._links = characters.link(self._links, name, self._profile)
        self._on_change(self._links)
        self.name.set("")
        self._fill_list()

    def _remove(self, name: str) -> None:
        self._links = characters.unlink(self._links, name)
        self._on_change(self._links)
        self._fill_list()
        self.field.entry.focus_set()

    def _done(self) -> None:
        self._close()


class CopyFromDialog(_Popup):
    """Pick one of `sources`; Replace calls on_ok(source) to copy its mirrors into `profile`."""

    def __init__(
        self,
        root: tk.Misc,
        profile: str,
        sources: Sequence[str],
        center: Point,
        on_ok: Callable[[str], None],
    ) -> None:
        super().__init__(root, tr("Copy from profile"))
        self._on_ok = on_ok
        self._source = DropdownField(
            self.body,
            [(name, name) for name in sources],
            sources[0],
            width=self.inner_width,
            background=theme.BG,
            on_pick=lambda _name: None,
        )
        self._source.pack(anchor="w", padx=px(PAD))
        tk.Label(
            self.body,
            text=tr(
                'Replaces the mirrors of "{name}" with those of the chosen profile. '
                "Until you save, Revert brings them back.",
                name=profile,
            ),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=self.inner_width,
        ).pack(fill="x", padx=px(PAD), pady=(px(8), 0))
        self._button_row(
            [Choice(tr("Cancel"), self._close), Choice(tr("Replace"), self._ok, "primary")]
        )
        self.win.bind("<Return>", lambda e: self._ok())
        self.win.bind("<KP_Enter>", lambda e: self._ok())
        self._open(center, self._close)

    def _ok(self) -> None:
        self._close()
        self._on_ok(self._source.value)
