"""App-wide constants and paths: the values to tune the app's behaviour and look."""

import os
from pathlib import Path

# The package's folder (in the .exe, inside the temp folder it unpacks to).
PACKAGE_DIR = Path(__file__).resolve().parent
# Everything the app writes; the .exe and a run from source share it.
DATA_DIR = Path(os.environ.get("APPDATA") or Path.home()) / "Tibia Mirror"
PROFILES_DIR = DATA_DIR / "profiles"
SETTINGS_FILE = DATA_DIR / "settings.json"
# Errors and crashes (the .exe has no console); trimmed on start once this big.
ERROR_LOG = DATA_DIR / "error.log"
ERROR_LOG_MAX_BYTES = 1_000_000
# The app's icon, in every size Windows asks for.
ICON_FILE = PACKAGE_DIR / "assets" / "icon.ico"
# Windows groups taskbar buttons by this; it must stay the same across versions.
APP_ID = "micky-mirror.TibiaMirror"
DEFAULT_PROFILE = "Default"

# Pixel sizes of the app's own look (frames, grip, gaps) are at 100% display
# scaling and go through ui/scale.px() where used; game pixels never do.

# Mirror zoom limits (1.0 = actual size).
ZOOM_RANGE = (0.25, 4.0)
# How close to a mirror's bottom-right corner the pointer must be to resize it.
RESIZE_GRIP = 14
# Position for very old saved regions without one.
DEFAULT_MIRROR_POS = (40, 40)
# A new mirror is placed this far from the area it mirrors.
NEW_MIRROR_GAP = 12

# Mirror opacity: new mirrors start at DEFAULT_OPACITY; the slider goes MIN_OPACITY..1.
DEFAULT_OPACITY = 0.5
MIN_OPACITY = 0.1
OPACITY_STEP = 0.05

# Frame colours ("default" is the theme's grey), shown in rows: soft shades,
# then deep ones. Coloured frames are COLOR_BORDER wide, to read at a glance.
FRAME_COLORS = (
    *("default", "red", "orange", "yellow", "green", "teal", "blue", "purple"),
    *("white", "deep_red", "deep_orange", "deep_yellow"),
    *("deep_green", "deep_teal", "deep_blue", "deep_purple"),
)
FRAME_COLORS_PER_ROW = 8
COLOR_BORDER = 2
# Windows 11's small corner rounding, in pixels at 100% display scaling.
ROUND_SMALL_RADIUS = 4

# Timers: alert range in seconds (0:01-59:59), the choices (the first is the
# default), and how often running timers are redrawn.
TIMER_ALERT_RANGE = (1, 59 * 60 + 59)
TIMER_DIRECTIONS = ("down", "up")
TIMER_BUTTONS = ("both", "left", "right")
TIMER_SOUNDS = ("asterisk", "exclamation", "notification", "critical", "beep", "none")
TIMER_TICK_MS = 200

# The panel's colour themes and languages; the first of each is the default.
THEMES = ("dark", "light")
LANGUAGES = ("en", "pl")

# Mirrors fade in and out over this long.
FADE_MS = 200

# Grey mirror frame, and the wider accent frame while its card is hovered.
MIRROR_BORDER = 1
HIGHLIGHT_BORDER = 3

# Longest region or profile name accepted by the name dialog.
MAX_NAME_LENGTH = 40

# Drags smaller than this (on either axis) are treated as accidental clicks.
MIN_SELECTION_SIDE = 5

# Saves wait for edits to settle, so a dragged slider doesn't write every step.
AUTOSAVE_DELAY_MS = 500
SETTINGS_SAVE_DELAY_MS = 300

VISIBILITY_POLL_MS = 200
ATTACH_POLL_MS = 1000
# Clicks and key presses seen anywhere are passed on this often (see rawinput).
INPUT_POLL_MS = 15

# 100px menu rail + 400px page; tall enough for the whole Settings page.
# Shorter screens get a shorter panel (geometry.panel_geometry), and pages scroll.
# The panel sizes are at 100% display scaling; the App scales them (ui/scale.py).
PANEL_SIZE = (500, 996)
# Title bar and borders (39px at 100% scaling): 996 + 40 fits a 1080p screen.
PANEL_FRAME = 40
PANEL_MIN_SIZE = (500, 440)
