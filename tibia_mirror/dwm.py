"""DWM thumbnails: the compositor draws a live copy of part of another window.

This is the core of the app. No capture, no injection - see docs/architecture.md.
"""

import ctypes
import sys
from ctypes import wintypes

from tibia_mirror import win32
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.win32 import RECT

dwmapi = ctypes.windll.dwmapi

DWM_TNP_RECTDESTINATION = 0x1
DWM_TNP_RECTSOURCE = 0x2
DWM_TNP_OPACITY = 0x4
DWM_TNP_VISIBLE = 0x8
DWM_TNP_SOURCECLIENTAREAONLY = 0x10
# Dark title bar: attribute 20 on Windows 10 20H1+ and 11, 19 on older Windows 10 builds.
DWMWA_USE_IMMERSIVE_DARK_MODE = (20, 19)
# Windows 11 corner rounding and window border.
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_BORDER_COLOR = 34
DWMWCP_DONOTROUND = 1
DWMWCP_ROUND = 2
DWMWCP_ROUNDSMALL = 3
DWMWA_COLOR_NONE = 0xFFFFFFFE


class DWM_THUMBNAIL_PROPERTIES(ctypes.Structure):  # noqa: N801 - Win32 name
    _fields_ = [
        ("dwFlags", wintypes.DWORD),
        ("rcDestination", RECT),
        ("rcSource", RECT),
        ("opacity", ctypes.c_ubyte),
        ("fVisible", wintypes.BOOL),
        ("fSourceClientAreaOnly", wintypes.BOOL),
    ]


HRESULT = ctypes.c_long
dwmapi.DwmRegisterThumbnail.restype = HRESULT
dwmapi.DwmRegisterThumbnail.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.POINTER(wintypes.HANDLE),
]
dwmapi.DwmUpdateThumbnailProperties.restype = HRESULT
dwmapi.DwmUpdateThumbnailProperties.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(DWM_THUMBNAIL_PROPERTIES),
]
dwmapi.DwmUnregisterThumbnail.restype = HRESULT
dwmapi.DwmUnregisterThumbnail.argtypes = [wintypes.HANDLE]
dwmapi.DwmSetWindowAttribute.restype = HRESULT
dwmapi.DwmSetWindowAttribute.argtypes = [
    wintypes.HWND,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
]


def _check(result: int, what: str) -> None:
    """Raise if a DWM call's result (an HRESULT: negative on failure) says it failed."""
    if result < 0:
        raise OSError(f"{what} failed: HRESULT {result & 0xFFFFFFFF:#010x}")


def set_dark_title_bar(hwnd: Hwnd, dark: bool) -> None:
    """Draw the window's title bar dark or light; silently does nothing where unsupported."""
    value = wintypes.BOOL(dark)
    for attribute in DWMWA_USE_IMMERSIVE_DARK_MODE:
        result = dwmapi.DwmSetWindowAttribute(
            hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
        )
        if result >= 0:
            win32.redraw_frame(hwnd)  # otherwise it only changes on the next activation
            return


def set_rounded_corners(hwnd: Hwnd, rounded: bool) -> None:
    """Round the window's corners with Windows 11's small rounding, or square them.

    The only rounding that also clips a DWM thumbnail. It adds a faint shadow
    that can't be turned off. Does nothing on Windows 10.
    """
    for attribute, value in (
        (DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUNDSMALL if rounded else DWMWCP_DONOTROUND),
        (DWMWA_BORDER_COLOR, DWMWA_COLOR_NONE),
    ):
        dword = wintypes.DWORD(value)
        dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(dword), ctypes.sizeof(dword))


# Windows 11 (build 22000) rounds windows' corners on request; Windows 10 cannot.
ROUNDED_POPUPS = sys.getwindowsversion().build >= 22000
# Popups draw their own 1px frame only where Windows cannot draw a rounded one.
POPUP_FRAME = 0 if ROUNDED_POPUPS else 1


def round_popup(hwnd: Hwnd, border: str, small: bool = False) -> None:
    """Give a popup Windows 11's rounded corners, shadow and a 1px `border` ("#rrggbb")."""
    if not ROUNDED_POPUPS:
        return
    red, green, blue = int(border[1:3], 16), int(border[3:5], 16), int(border[5:7], 16)
    for attribute, value in (
        (DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUNDSMALL if small else DWMWCP_ROUND),
        (DWMWA_BORDER_COLOR, red | green << 8 | blue << 16),  # a COLORREF is 0x00BBGGRR
    ):
        dword = wintypes.DWORD(value)
        dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(dword), ctypes.sizeof(dword))


class Thumbnail:
    """A live copy of a client-area rect of `source_hwnd`, drawn into `dest_hwnd`."""

    def __init__(self, dest_hwnd: Hwnd, source_hwnd: Hwnd) -> None:
        self._handle = wintypes.HANDLE()
        _check(
            dwmapi.DwmRegisterThumbnail(dest_hwnd, source_hwnd, ctypes.byref(self._handle)),
            "DwmRegisterThumbnail",
        )

    def show(self, source: Rect, dest: Rect) -> None:
        """Draw `source` (source client coords) scaled into `dest` (our client coords)."""
        properties = DWM_THUMBNAIL_PROPERTIES()
        properties.dwFlags = (
            DWM_TNP_RECTDESTINATION
            | DWM_TNP_RECTSOURCE
            | DWM_TNP_VISIBLE
            | DWM_TNP_OPACITY
            | DWM_TNP_SOURCECLIENTAREAONLY
        )
        properties.opacity = 255
        properties.fVisible = True
        properties.fSourceClientAreaOnly = True
        properties.rcSource = RECT(source.x, source.y, source.right, source.bottom)
        properties.rcDestination = RECT(dest.x, dest.y, dest.right, dest.bottom)
        _check(
            dwmapi.DwmUpdateThumbnailProperties(self._handle, ctypes.byref(properties)),
            "DwmUpdateThumbnailProperties",
        )

    def close(self) -> None:
        if self._handle:
            dwmapi.DwmUnregisterThumbnail(self._handle)
            self._handle = wintypes.HANDLE()
