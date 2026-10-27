"""Modal popups: names and choices."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from tibia_mirror.config import MAX_NAME_LENGTH
from tibia_mirror.core.geometry import Point
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.render import margins
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.widgets import RaisedButton, TextField
from tibia_mirror.winapi import dwm, win32

# Sizes at 100% display scaling, scaled with px() where used.
WIDTH = 340
PAD = 18
BUTTON_GAP = 12
BUTTON_HEIGHT = 34
BUTTONS_GAP_ABOVE = 16  # between the content and the button row
# The popup's border, 1px on each side: Windows draws it (or _Popup does, on
# Windows 10), and it stays 1px at any scaling.
BORDER = 2


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
