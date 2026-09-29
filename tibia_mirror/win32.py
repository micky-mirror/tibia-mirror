"""ctypes bindings for every Win32 call the app makes, plus thin helpers.

Each function's argtypes/restype is declared here, so handles are never truncated.
Terms: an HWND is a window's handle; a virtual-key code (`vk`) is a key's number,
whatever the keyboard layout (0x74 is F5).
"""

import ctypes
import tkinter as tk
from ctypes import wintypes
from typing import Any

from tibia_mirror.geometry import Rect
from tibia_mirror.handles import Hwnd

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32
shell32 = ctypes.windll.shell32
# For calls whose result is read from GetLastError, which other calls could overwrite.
kernel32_le = ctypes.WinDLL("kernel32", use_last_error=True)

GA_ROOT = 2
SW_RESTORE = 9
MONITOR_DEFAULTTONEAREST = 2
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x20
WS_EX_LAYERED = 0x80000
LWA_ALPHA = 2
RGN_DIFF = 4
SWP_NOSIZE = 0x1
SWP_NOMOVE = 0x2
SWP_NOZORDER = 0x4
SWP_NOACTIVATE = 0x10
SWP_FRAMECHANGED = 0x20
MB_ICONERROR = 0x10
ERROR_ALREADY_EXISTS = 183
WAIT_OBJECT_0 = 0
ASFW_ANY = 0xFFFFFFFF


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


# Any: ctypes' foreign functions and C types have no useful static types.
def _sig(function: Any, restype: Any, *argtypes: Any) -> None:  # noqa: ANN401
    function.restype = restype
    function.argtypes = list(argtypes)


_sig(user32.SetProcessDPIAware, wintypes.BOOL)
_sig(shell32.SetCurrentProcessExplicitAppUserModelID, ctypes.HRESULT, wintypes.LPCWSTR)
_sig(
    user32.MessageBoxW,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.UINT,
)
_sig(user32.GetForegroundWindow, wintypes.HWND)
_sig(user32.GetAncestor, wintypes.HWND, wintypes.HWND, wintypes.UINT)
_sig(user32.MonitorFromWindow, wintypes.HMONITOR, wintypes.HWND, wintypes.DWORD)
_sig(user32.MonitorFromPoint, wintypes.HMONITOR, POINT, wintypes.DWORD)
_sig(user32.GetMonitorInfoW, wintypes.BOOL, wintypes.HMONITOR, ctypes.POINTER(MONITORINFO))
_sig(user32.ClientToScreen, wintypes.BOOL, wintypes.HWND, ctypes.POINTER(POINT))
_sig(user32.GetClientRect, wintypes.BOOL, wintypes.HWND, ctypes.POINTER(RECT))
_sig(user32.GetCursorPos, wintypes.BOOL, ctypes.POINTER(POINT))
_sig(user32.WindowFromPoint, wintypes.HWND, POINT)
_sig(user32.MapVirtualKeyW, wintypes.UINT, wintypes.UINT, wintypes.UINT)
_sig(user32.GetKeyState, ctypes.c_short, ctypes.c_int)
_sig(user32.GetKeyNameTextW, ctypes.c_int, wintypes.LONG, wintypes.LPWSTR, ctypes.c_int)
_sig(user32.EnumWindows, wintypes.BOOL, WNDENUMPROC, wintypes.LPARAM)
_sig(user32.IsWindowVisible, wintypes.BOOL, wintypes.HWND)
_sig(user32.GetWindowTextLengthW, ctypes.c_int, wintypes.HWND)
_sig(user32.GetWindowTextW, ctypes.c_int, wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
_sig(user32.GetWindowThreadProcessId, wintypes.DWORD, wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
_sig(kernel32.OpenProcess, wintypes.HANDLE, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
_sig(
    kernel32.QueryFullProcessImageNameW,
    wintypes.BOOL,
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
)
_sig(kernel32.CloseHandle, wintypes.BOOL, wintypes.HANDLE)
_sig(user32.GetClassNameW, ctypes.c_int, wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
_sig(user32.IsIconic, wintypes.BOOL, wintypes.HWND)
_sig(user32.IsWindow, wintypes.BOOL, wintypes.HWND)
_sig(user32.ShowWindow, wintypes.BOOL, wintypes.HWND, ctypes.c_int)
_sig(user32.SetForegroundWindow, wintypes.BOOL, wintypes.HWND)
_sig(user32.AllowSetForegroundWindow, wintypes.BOOL, wintypes.DWORD)
_sig(kernel32_le.CreateMutexW, wintypes.HANDLE, wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
_sig(
    kernel32.CreateEventW,
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.BOOL,
    wintypes.BOOL,
    wintypes.LPCWSTR,
)
_sig(kernel32.SetEvent, wintypes.BOOL, wintypes.HANDLE)
_sig(kernel32.WaitForSingleObject, wintypes.DWORD, wintypes.HANDLE, wintypes.DWORD)
_sig(
    user32.SetWindowPos,
    wintypes.BOOL,
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
)
_sig(user32.GetWindowLongW, wintypes.LONG, wintypes.HWND, ctypes.c_int)
_sig(user32.GetDpiForWindow, wintypes.UINT, wintypes.HWND)
_sig(user32.SetWindowRgn, ctypes.c_int, wintypes.HWND, wintypes.HANDLE, wintypes.BOOL)
_sig(gdi32.CreateRoundRectRgn, wintypes.HANDLE, *[ctypes.c_int] * 6)
_sig(gdi32.CreateRectRgn, wintypes.HANDLE, *[ctypes.c_int] * 4)
_sig(
    gdi32.CombineRgn, ctypes.c_int, wintypes.HANDLE, wintypes.HANDLE, wintypes.HANDLE, ctypes.c_int
)
_sig(gdi32.DeleteObject, wintypes.BOOL, wintypes.HANDLE)
_sig(user32.SetWindowLongW, wintypes.LONG, wintypes.HWND, ctypes.c_int, wintypes.LONG)
_sig(
    user32.SetLayeredWindowAttributes,
    wintypes.BOOL,
    wintypes.HWND,
    wintypes.COLORREF,
    wintypes.BYTE,
    wintypes.DWORD,
)


def enable_dpi_awareness() -> None:
    """Make Win32 coordinates physical pixels. Call before creating any window."""
    user32.SetProcessDPIAware()


def set_app_id(app_id: str) -> None:
    """Give the app its own taskbar button and icon, not python.exe's. Call before any window."""
    shell32.SetCurrentProcessExplicitAppUserModelID(app_id)


def error_box(title: str, text: str) -> None:
    """A plain Windows error message, for when the app's own windows can't be shown."""
    user32.MessageBoxW(None, text, title, MB_ICONERROR)


def toplevel_hwnd(widget: tk.Misc) -> Hwnd:
    """The real top-level HWND of a Tk window (winfo_id is an inner child)."""
    widget.update_idletasks()
    hwnd: Hwnd = user32.GetAncestor(widget.winfo_id(), GA_ROOT)
    return hwnd


def foreground_window() -> Hwnd | None:
    # A NULL handle comes back as None: no window has the focus (e.g. mid-switch).
    hwnd: Hwnd | None = user32.GetForegroundWindow()
    return hwnd


def _monitor_info(hmonitor: int) -> MONITORINFO:
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    user32.GetMonitorInfoW(hmonitor, ctypes.byref(info))
    return info


def _rect(edges: RECT) -> Rect:
    """A Win32 RECT (left, top, right, bottom) as a Rect (x, y, width, height)."""
    return Rect(edges.left, edges.top, edges.right - edges.left, edges.bottom - edges.top)


def monitor_rect(hwnd: Hwnd) -> Rect:
    """The monitor the window is mostly on, in screen coordinates."""
    hmonitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    return _rect(_monitor_info(hmonitor).rcMonitor)


def work_area_at(point: tuple[int, int]) -> Rect:
    """The work area (monitor minus taskbar) containing a screen point."""
    hmonitor = user32.MonitorFromPoint(POINT(*point), MONITOR_DEFAULTTONEAREST)
    return _rect(_monitor_info(hmonitor).rcWork)


def client_origin(hwnd: Hwnd) -> tuple[int, int]:
    """Screen position of the window's client-area top-left corner."""
    point = POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y


def client_rect(hwnd: Hwnd) -> Rect:
    """The window's client area (inside its frame) in screen coordinates."""
    size = RECT()  # GetClientRect gives the size: its left and top are always 0
    user32.GetClientRect(hwnd, ctypes.byref(size))
    x, y = client_origin(hwnd)
    return Rect(x, y, size.right, size.bottom)


def cursor_pos() -> tuple[int, int]:
    """The mouse pointer's position in screen coordinates."""
    point = POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def toplevel_at(x: int, y: int) -> Hwnd | None:
    """The top-level window at a screen point: the one a click there goes to."""
    hwnd = user32.WindowFromPoint(POINT(x, y))
    return user32.GetAncestor(hwnd, GA_ROOT) if hwnd else None


# Keys whose scan code needs the "extended" bit for GetKeyNameText to name them right.
_EXTENDED_KEYS = frozenset(
    {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x6F, 0x90, 0xA3, 0xA5}
)
MAPVK_VK_TO_VSC = 0


def key_name(vk: int) -> str:
    """A virtual key's name as the keyboard layout writes it ("F5", "Q", "Num 1", ...)."""
    scan_code = user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC)
    extended = 1 << 24 if vk in _EXTENDED_KEYS else 0
    buffer = ctypes.create_unicode_buffer(64)
    if scan_code and user32.GetKeyNameTextW((scan_code << 16) | extended, buffer, len(buffer)):
        return buffer.value
    return f"Key {vk}"


def modifiers_down() -> tuple[str, ...]:
    """Names of the modifier keys held right now, in order ("ctrl", "shift", "alt")."""
    modifier_keys = (("ctrl", 0x11), ("shift", 0x10), ("alt", 0x12))
    return tuple(name for name, vk in modifier_keys if user32.GetKeyState(vk) & 0x8000)


def window_title(hwnd: Hwnd) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def visible_windows() -> list[Hwnd]:
    """HWNDs of all visible top-level windows, in z-order."""
    found: list[Hwnd] = []

    def collect(hwnd: Hwnd, _lparam: int) -> bool:
        if user32.IsWindowVisible(hwnd):
            found.append(hwnd)
        return True

    user32.EnumWindows(WNDENUMPROC(collect), 0)
    return found


def process_image_path(hwnd: Hwnd) -> str:
    """The executable path of the window's process, or "". Needs no memory access."""
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, window_process_id(hwnd))
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buffer = ctypes.create_unicode_buffer(size.value)
        ok = kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size))
        return buffer.value if ok else ""
    finally:
        kernel32.CloseHandle(handle)


def window_class(hwnd: Hwnd) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, len(buffer))
    return buffer.value


def window_process_id(hwnd: Hwnd) -> int:
    process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    return process_id.value


def is_window(hwnd: Hwnd) -> bool:
    """Whether hwnd still names a window (False once its program has closed it)."""
    return bool(user32.IsWindow(hwnd))


def is_minimized(hwnd: Hwnd) -> bool:
    return bool(user32.IsIconic(hwnd))


def bring_to_front(hwnd: Hwnd) -> None:
    """Restore (if minimized) and focus a window: only the app's panel, never Tibia.

    Windows allows it only while this process is in front, or after another one
    called allow_any_to_take_foreground().
    """
    if is_minimized(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)


def allow_any_to_take_foreground() -> None:
    """Let another process take the foreground; works only while this one is in front."""
    user32.AllowSetForegroundWindow(ASFW_ANY)


def create_mutex(name: str) -> tuple[int, bool]:
    """Open or create the named mutex: (handle, whether it already existed)."""
    handle: int = kernel32_le.CreateMutexW(None, False, name)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle, ctypes.get_last_error() == ERROR_ALREADY_EXISTS


def create_event(name: str) -> int:
    """Open the named auto-reset event, creating it unset if needed."""
    handle: int = kernel32.CreateEventW(None, False, False, name)
    if not handle:
        raise ctypes.WinError()
    return handle


def set_event(handle: int) -> None:
    kernel32.SetEvent(handle)


def take_event(handle: int) -> bool:
    """Whether the event was set; taking it unsets it (auto-reset). Never waits."""
    return bool(kernel32.WaitForSingleObject(handle, 0) == WAIT_OBJECT_0)


def redraw_frame(hwnd: Hwnd) -> None:
    """Make Windows repaint the title bar and borders, leaving position, size and order alone."""
    flags = SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, flags)


def dpi_scale(hwnd: Hwnd) -> float:
    """The window's display scaling (1.0 at 100%, 1.25 at 125%, ...)."""
    dpi: int = user32.GetDpiForWindow(hwnd)
    return dpi / 96


def _rounded_rect_region(x: int, y: int, w: int, h: int, radius: int) -> int:
    # A region's right and bottom are exclusive, hence the +1 for the rounded kind.
    region: int
    if radius <= 0:
        region = gdi32.CreateRectRgn(x, y, x + w, y + h)
    else:
        region = gdi32.CreateRoundRectRgn(x, y, x + w + 1, y + h + 1, 2 * radius, 2 * radius)
    return region


def set_ring_shape(
    hwnd: Hwnd, width: int, height: int, radius: int, hole: tuple[int, int, int, int, int] | None
) -> None:
    """Shape the window as a (rounded) rect minus `hole` (x, y, w, h, radius), or solid.

    Windows owns the region once set, so it is not freed here.
    """
    region = _rounded_rect_region(0, 0, width, height, radius)
    if hole is not None:
        inner = _rounded_rect_region(*hole)
        gdi32.CombineRgn(region, region, inner, RGN_DIFF)
        gdi32.DeleteObject(inner)
    user32.SetWindowRgn(hwnd, region, True)


def _set_ex_style(hwnd: Hwnd, flag: int, enabled: bool) -> None:
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | flag if enabled else style & ~flag)


def set_alpha(hwnd: Hwnd, alpha: float) -> None:
    """Whole-window opacity, 0..1.

    Unlike Tk's -alpha, it keeps the layered style at full opacity, so
    click-through still works.
    """
    _set_ex_style(hwnd, WS_EX_LAYERED, True)
    user32.SetLayeredWindowAttributes(hwnd, 0, round(alpha * 255), LWA_ALPHA)


def set_click_through(hwnd: Hwnd, enabled: bool) -> None:
    """Let mouse input pass through the window (it must be layered, see set_alpha)."""
    _set_ex_style(hwnd, WS_EX_TRANSPARENT, enabled)
