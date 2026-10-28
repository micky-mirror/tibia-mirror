"""Clicks and key presses from anywhere, via Windows Raw Input (read-only).

Warning: the window procedure runs inside Tk's event loop and must never call Tk,
or Python crashes ("PyEval_RestoreThread"). See docs/architecture.md, "Input and timers".
"""

import ctypes
from collections.abc import Callable
from ctypes import wintypes
from typing import Any

from tibia_mirror.core.handles import Hwnd

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_INPUT = 0x00FF
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIDEV_INPUTSINK = 0x00000100
RI_MOUSE_LEFT_BUTTON_DOWN = 0x0001
RI_KEY_BREAK = 0x01  # set on key up
HWND_MESSAGE = -3
USAGE_PAGE_GENERIC = 0x01
USAGE_MOUSE = 0x02
USAGE_KEYBOARD = 0x06

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
READ_FAILED = 0xFFFFFFFF  # what GetRawInputData gives on an error: -1 as a UINT


class RawInputWindow:
    """A hidden window that hears the mouse and the keyboard of the whole computer."""

    def __init__(
        self,
        on_left_down: Callable[[], None],
        on_key_change: Callable[[int, bool], None],
    ) -> None:
        self._on_left_down = on_left_down  # called when the left mouse button goes down
        self._on_key_change = on_key_change  # called with the key code, and True when it goes down
        # Windows calls this, so it is kept for as long as the window lives
        self._window_procedure = WNDPROC(self._on_message)
        # create the hidden window and send it all input
        self._register_window_class()
        window_handle = self._create_window()
        self._register_devices(window_handle)

    def _register_window_class(self) -> None:
        window_class = WNDCLASSEXW()
        window_class.cbSize = ctypes.sizeof(WNDCLASSEXW)
        window_class.lpfnWndProc = self._window_procedure
        window_class.hInstance = kernel32.GetModuleHandleW(None)
        window_class.lpszClassName = CLASS_NAME

        if not user32.RegisterClassExW(ctypes.byref(window_class)):
            raise ctypes.WinError()

    def _create_window(self) -> Hwnd:
        """A message-only window: it is never shown, it only gets messages."""
        window_handle: Hwnd | None = user32.CreateWindowExW(
            0,
            CLASS_NAME,
            None,
            0,
            0,
            0,
            0,
            0,
            HWND_MESSAGE,
            None,
            kernel32.GetModuleHandleW(None),
            None,
        )
        if not window_handle:
            raise ctypes.WinError()

        return window_handle

    def _register_devices(self, window_handle: Hwnd) -> None:
        """Send the mouse and keyboard input to the window, also while the app is not in front."""
        devices = (RAWINPUTDEVICE * 2)(
            RAWINPUTDEVICE(USAGE_PAGE_GENERIC, USAGE_MOUSE, RIDEV_INPUTSINK, window_handle),
            RAWINPUTDEVICE(USAGE_PAGE_GENERIC, USAGE_KEYBOARD, RIDEV_INPUTSINK, window_handle),
        )
        if not user32.RegisterRawInputDevices(devices, len(devices), ctypes.sizeof(RAWINPUTDEVICE)):
            raise ctypes.WinError()

    def _on_message(self, window_handle: Hwnd, message: int, wparam: int, lparam: int) -> int:
        if message == WM_INPUT:
            self._read_input(lparam)

        result: int = user32.DefWindowProcW(window_handle, message, wparam, lparam)
        return result

    def _read_input(self, input_handle: int) -> None:
        event = RAWINPUT()
        size = wintypes.UINT(ctypes.sizeof(event))
        copied = user32.GetRawInputData(
            input_handle,
            RID_INPUT,
            ctypes.byref(event),
            ctypes.byref(size),
            ctypes.sizeof(RAWINPUTHEADER),
        )
        if copied in (0, READ_FAILED):
            return

        if event.header.dwType == RIM_TYPEMOUSE:
            self._read_mouse(event.data.mouse)
        elif event.header.dwType == RIM_TYPEKEYBOARD:
            self._read_keyboard(event.data.keyboard)

    def _read_mouse(self, mouse: RAWMOUSE) -> None:
        if mouse.u.buttons.usButtonFlags & RI_MOUSE_LEFT_BUTTON_DOWN:
            self._on_left_down()

    def _read_keyboard(self, keyboard: RAWKEYBOARD) -> None:
        is_down = not keyboard.Flags & RI_KEY_BREAK
        self._on_key_change(keyboard.VKey, is_down)
