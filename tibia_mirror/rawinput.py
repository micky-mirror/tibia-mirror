"""Clicks and key presses from anywhere, via Windows Raw Input (read-only).

Warning: the window procedure runs inside Tk's event loop and must never call Tk,
or Python crashes ("PyEval_RestoreThread"). It only queues events; a Tk timer
passes them on. See docs/architecture.md, "Input and timers".
"""

import ctypes
import time
import tkinter as tk
from collections import deque
from collections.abc import Callable
from ctypes import wintypes
from functools import partial
from typing import Any

from tibia_mirror import win32
from tibia_mirror.config import INPUT_POLL_MS
from tibia_mirror.handles import Hwnd

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_INPUT = 0x00FF
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIDEV_INPUTSINK = 0x00000100
RIDEV_REMOVE = 0x00000001
RI_MOUSE_LEFT_BUTTON_DOWN = 0x0001
RI_MOUSE_RIGHT_BUTTON_DOWN = 0x0004
RI_KEY_BREAK = 0x01  # set on key up
HWND_MESSAGE = -3
USAGE_PAGE_GENERIC = 0x01
USAGE_MOUSE = 0x02
USAGE_KEYBOARD = 0x06
# Modifier keys by name, generic and left/right codes alike (Raw Input may report either).
MODIFIER_KEYS = {
    "ctrl": {0x11, 0xA2, 0xA3},
    "shift": {0x10, 0xA0, 0xA1},
    "alt": {0x12, 0xA4, 0xA5},
}
ALL_MODIFIER_KEYS: set[int] = set().union(*MODIFIER_KEYS.values())

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
        ("hIconSm", wintypes.HICON),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", wintypes.USHORT),
        ("usUsage", wintypes.USHORT),
        ("dwFlags", wintypes.DWORD),
        ("hwndTarget", wintypes.HWND),
    ]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSize", wintypes.DWORD),
        ("hDevice", wintypes.HANDLE),
        ("wParam", wintypes.WPARAM),
    ]


class _MouseButtons(ctypes.Structure):
    _fields_ = [("usButtonFlags", wintypes.USHORT), ("usButtonData", wintypes.USHORT)]


class _MouseButtonsUnion(ctypes.Union):
    _fields_ = [("ulButtons", wintypes.ULONG), ("buttons", _MouseButtons)]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [
        ("usFlags", wintypes.USHORT),
        ("u", _MouseButtonsUnion),
        ("ulRawButtons", wintypes.ULONG),
        ("lLastX", wintypes.LONG),
        ("lLastY", wintypes.LONG),
        ("ulExtraInformation", wintypes.ULONG),
    ]


class RAWKEYBOARD(ctypes.Structure):
    _fields_ = [
        ("MakeCode", wintypes.USHORT),
        ("Flags", wintypes.USHORT),
        ("Reserved", wintypes.USHORT),
        ("VKey", wintypes.USHORT),
        ("Message", wintypes.UINT),
        ("ExtraInformation", wintypes.ULONG),
    ]


class _RawData(ctypes.Union):
    _fields_ = [("mouse", RAWMOUSE), ("keyboard", RAWKEYBOARD)]


class RAWINPUT(ctypes.Structure):
    _fields_ = [("header", RAWINPUTHEADER), ("data", _RawData)]


# Any: ctypes' foreign functions and C types have no useful static types.
def _sig(function: Any, restype: Any, *argtypes: Any) -> None:  # noqa: ANN401
    function.restype = restype
    function.argtypes = list(argtypes)


_sig(kernel32.GetModuleHandleW, wintypes.HMODULE, wintypes.LPCWSTR)
_sig(user32.RegisterClassExW, wintypes.ATOM, ctypes.POINTER(WNDCLASSEXW))
_sig(user32.UnregisterClassW, wintypes.BOOL, wintypes.LPCWSTR, wintypes.HINSTANCE)
_sig(
    user32.CreateWindowExW,
    wintypes.HWND,
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    wintypes.LPVOID,
)
_sig(user32.DestroyWindow, wintypes.BOOL, wintypes.HWND)
_sig(user32.DefWindowProcW, LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
_sig(
    user32.RegisterRawInputDevices,
    wintypes.BOOL,
    ctypes.POINTER(RAWINPUTDEVICE),
    wintypes.UINT,
    wintypes.UINT,
)
_sig(
    user32.GetRawInputData,
    wintypes.UINT,
    wintypes.HANDLE,
    wintypes.UINT,
    wintypes.LPVOID,
    ctypes.POINTER(wintypes.UINT),
    wintypes.UINT,
)

CLASS_NAME = "TibiaMirrorRawInput"


class InputWatcher:
    """Reports on_click(button, x, y, at) and on_key(vk, modifiers) from anywhere.

    start(widget) begins and stop() ends; the callbacks run from Tk's loop. Held-key
    repeats and a modifier pressed on its own are ignored.
    """

    def __init__(
        self,
        on_click: Callable[[str, int, int, float], None],
        on_key: Callable[[int, tuple[str, ...]], None],
    ) -> None:
        self._on_click, self._on_key = on_click, on_key
        self._held: set[int] = set()  # keys down now, so auto-repeat is not a new press
        self._pending: deque[Callable[[], None]] = deque()  # noted, not yet passed on
        self._proc = WNDPROC(self._window_proc)  # kept alive for as long as the window
        self._hwnd: Hwnd | None = None
        self._instance: int | None = kernel32.GetModuleHandleW(None)
        self._widget: tk.Misc | None = None
        self._poll_job: str | None = None

    def start(self, widget: tk.Misc) -> None:
        self._widget = widget
        self._poll()
        window_class = WNDCLASSEXW()
        window_class.cbSize = ctypes.sizeof(WNDCLASSEXW)
        window_class.lpfnWndProc = self._proc
        window_class.hInstance = self._instance
        window_class.lpszClassName = CLASS_NAME
        if not user32.RegisterClassExW(ctypes.byref(window_class)):
            raise ctypes.WinError()
        self._hwnd = user32.CreateWindowExW(
            0, CLASS_NAME, None, 0, 0, 0, 0, 0, HWND_MESSAGE, None, self._instance, None
        )
        if not self._hwnd:
            raise ctypes.WinError()
        self._register(RIDEV_INPUTSINK, self._hwnd)

    def stop(self) -> None:
        if self._widget is not None and self._poll_job is not None:
            self._widget.after_cancel(self._poll_job)
        self._widget, self._poll_job = None, None
        self._pending.clear()
        if self._hwnd is None:
            return
        self._register(RIDEV_REMOVE, None)
        user32.DestroyWindow(self._hwnd)
        user32.UnregisterClassW(CLASS_NAME, self._instance)
        self._hwnd = None

    @staticmethod
    def _register(flags: int, hwnd: Hwnd | None) -> None:
        devices = (RAWINPUTDEVICE * 2)(
            RAWINPUTDEVICE(USAGE_PAGE_GENERIC, USAGE_MOUSE, flags, hwnd),
            RAWINPUTDEVICE(USAGE_PAGE_GENERIC, USAGE_KEYBOARD, flags, hwnd),
        )
        if not user32.RegisterRawInputDevices(devices, 2, ctypes.sizeof(RAWINPUTDEVICE)):
            raise ctypes.WinError()

    # Schedules its next run first, so an error in a callback cannot stop it for good.
    def _poll(self) -> None:
        assert self._widget is not None
        self._poll_job = self._widget.after(INPUT_POLL_MS, self._poll)
        self.dispatch()

    def dispatch(self) -> None:
        """Pass every noted event on to its callback, oldest first."""
        while self._pending:
            self._pending.popleft()()

    # No Tk from here on down: these run inside Tk's event loop (see the module warning).
    def _window_proc(self, hwnd: Hwnd, message: int, wparam: int, lparam: int) -> int:
        if message == WM_INPUT:
            self._handle(lparam)
        result: int = user32.DefWindowProcW(hwnd, message, wparam, lparam)
        return result

    def _handle(self, handle: int) -> None:
        event = RAWINPUT()
        size = wintypes.UINT(ctypes.sizeof(event))
        copied = user32.GetRawInputData(
            handle,
            RID_INPUT,
            ctypes.byref(event),
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        )
        if copied in (0, 0xFFFFFFFF):
            return
        if event.header.dwType == RIM_TYPEMOUSE:
            flags = event.data.mouse.u.buttons.usButtonFlags
            if flags & RI_MOUSE_LEFT_BUTTON_DOWN:
                self._note_click("left")
            if flags & RI_MOUSE_RIGHT_BUTTON_DOWN:
                self._note_click("right")
        elif event.header.dwType == RIM_TYPEKEYBOARD:
            key = event.data.keyboard
            self._note_key(key.VKey, down=not key.Flags & RI_KEY_BREAK)

    def _note_click(self, button: str) -> None:
        x, y = win32.cursor_pos()
        self._pending.append(partial(self._on_click, button, x, y, time.monotonic()))

    def _note_key(self, vk: int, down: bool) -> None:
        if not down:
            self._held.discard(vk)
        elif vk not in self._held:
            self._held.add(vk)
            if vk not in ALL_MODIFIER_KEYS:
                held = tuple(name for name, keys in MODIFIER_KEYS.items() if keys & self._held)
                self._pending.append(partial(self._on_key, vk, held))
