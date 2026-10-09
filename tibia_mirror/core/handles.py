"""Names for Windows handles, free of ctypes so the pure modules can use them too."""

# A window handle (HWND): the number Windows names a window by. Tk's inner
# frames are windows too, each with its own handle.
Hwnd = int
