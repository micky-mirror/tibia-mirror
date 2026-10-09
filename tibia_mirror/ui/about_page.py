"""The About page: what the app is for, its version, contact and tips, and the trademark notice."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Sequence

from tibia_mirror import __version__
from tibia_mirror.about import DISCORD, TIP_CHARACTER
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.widgets import CopyText, ScrollList

PARAGRAPH_GAP = 14  # at 100% display scaling


def build_about_page(parent: tk.Misc, *, width: int, pad: int) -> tk.Frame:
    """The About page, scrolling if a short window cuts it off; the credit is in the footer."""
    page = tk.Frame(parent, bg=theme.BG)
    scroll = ScrollList(page, width=width)
    scroll.pack(anchor="w", fill="y", expand=True, padx=(pad, 0), pady=(px(18), px(8)))
    column = scroll.inner

    # The app's name is never translated.
    tk.Label(column, text="Tibia Mirror", bg=theme.BG, fg=theme.TEXT, font=theme.FONT_TITLE).pack(
        anchor="w"
    )
    tk.Label(
        column,
        text=tr("Version {version}", version=__version__),
        bg=theme.BG,
        fg=theme.SUBTEXT,
        font=theme.FONT,
    ).pack(anchor="w")

    paragraph(
        column,
        tr(
            "Keep your eyes on the fight, not on the corners of the screen. "
            "Tibia Mirror puts the parts of Tibia you care about - cooldowns, "
            "the minimap, anything you like - into small windows you can place "
            "wherever suits you."
        ),
        theme.TEXT,
        width,
    )
    paragraph(
        column,
        tr(
            "It uses Windows' own window previews - the same ones you see on the taskbar. "
            "No screen capture, nothing changed in the game, nothing sent anywhere."
        ),
        theme.TEXT,
        width,
    )
    if DISCORD is not None:
        # The username gets a line of its own: after the question it wouldn't fit in Polish.
        before, after = tr("Questions or ideas? Message me on {discord}:").split("{discord}")
        rich_paragraph(
            column,
            [(before, theme.TEXT), (tr("Discord"), theme.BLURPLE), (after, theme.TEXT)],
            width,
        )
        CopyText(column, DISCORD, background=theme.BG, fg=theme.BLURPLE).pack(anchor="w")
    if TIP_CHARACTER is not None:
        # Optional: the app stays free either way. The footer has a short version.
        sentence = tr(
            "Tibia Mirror is free. If you find it useful, you can say thanks "
            "by sending {coins} to this character:"
        )
        before, after = sentence.split("{coins}")
        coins = tr("a few Tibia Coins")
        rich_paragraph(
            column, [(before, theme.TEXT), (coins, theme.GOLD), (after, theme.TEXT)], width
        )
        CopyText(column, TIP_CHARACTER, background=theme.BG, fg=theme.GOLD).pack(anchor="w")
    paragraph(
        column,
        tr(
            "A fan-made tool for the Tibia community. Tibia is a trademark of "
            "CipSoft GmbH, and this app is not affiliated with or endorsed by CipSoft."
        ),
        theme.SUBTEXT,
        width,
    )
    return page


def paragraph(column: tk.Misc, text: str, fg: str, width: int) -> None:
    tk.Label(
        column,
        text=text,
        bg=theme.BG,
        fg=fg,
        font=theme.FONT,
        justify="left",
        wraplength=width,
    ).pack(anchor="w", pady=(px(PARAGRAPH_GAP), 0))


def rich_paragraph(column: tk.Misc, parts: Sequence[tuple[str, str]], width: int) -> None:
    """Like paragraph(), but with each (text, colour) part in its own colour.

    A read-only tk.Text laid out like a Label (a Label has one colour). Its own
    bindings are dropped, so it can't be selected and the page still scrolls over it.
    """
    inset = 3  # a tk.Label's 2px border and 1px padding, on every side (Tk doesn't scale them)
    box = tk.Frame(column, bg=theme.BG, width=width + 2 * inset, height=1)
    box.pack_propagate(False)
    text = tk.Text(
        box,
        font=theme.FONT,
        bg=theme.BG,
        bd=0,
        highlightthickness=0,
        padx=inset,
        pady=inset,
        wrap="word",
        cursor="",
    )
    for i, (part, fg) in enumerate(parts):
        text.tag_configure(f"part{i}", foreground=fg)
        text.insert("end", part, f"part{i}")
    text.configure(state="disabled")
    text.bindtags((str(text), str(text.winfo_toplevel()), "all"))
    text.pack(fill="both", expand=True)
    box.pack(anchor="w", pady=(px(PARAGRAPH_GAP), 0))

    line = tkfont.Font(font=theme.FONT).metrics("linespace")

    def fit(_e: object = None) -> None:
        counted = text.count("1.0", "end", "displaylines")
        lines = counted[0] if isinstance(counted, tuple) else (counted or 1)
        box.configure(height=lines * line + 2 * inset)

    text.bind("<Configure>", fit)
