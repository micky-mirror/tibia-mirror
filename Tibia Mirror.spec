# PyInstaller build of the single-file dist\Tibia Mirror.exe. From the project folder:
#
#     .venv\Scripts\python -m PyInstaller "Tibia Mirror.spec"
#
# The name, version and copyright shown in the file's Properties come from the code.

import sys
from datetime import date
from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

ROOT = Path(SPECPATH)
sys.path.insert(0, str(ROOT))
from tibia_mirror import __version__  # noqa: E402
from tibia_mirror.about import AUTHOR, copyright_years  # noqa: E402

NAME = "Tibia Mirror"
VERSION = tuple(int(n) for n in __version__.split(".")) + (0,)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    datas=[(str(ROOT / "tibia_mirror" / "assets" / "icon.ico"), "tibia_mirror/assets")],
    # Reachable only through standard-library code the app never runs (uuid4, shutil's
    # copy functions, ...): left out, the .exe ships no OpenSSL, sockets or compression
    # libraries, and NOTICE.md stays short. A module here that the app does need
    # fails with ImportError only in the built .exe, so test it after changing this.
    excludes=[
        *("hashlib", "_hashlib", "ssl", "_ssl"),
        *("socket", "_socket", "select", "selectors"),
        *("bz2", "_bz2", "lzma", "_lzma"),
        *("decimal", "_decimal", "_pydecimal"),
    ],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name=NAME,
    icon=str(ROOT / "tibia_mirror" / "assets" / "icon.ico"),
    console=False,
    # UPX packing makes antivirus programs flag the .exe more often.
    upx=False,
    version=VSVersionInfo(
        ffi=FixedFileInfo(filevers=VERSION, prodvers=VERSION),
        kids=[
            StringFileInfo(
                [
                    StringTable(
                        "040904B0",  # US English, Unicode
                        [
                            StringStruct("ProductName", NAME),
                            StringStruct("FileDescription", NAME),
                            StringStruct("ProductVersion", __version__),
                            StringStruct("FileVersion", __version__),
                            StringStruct("OriginalFilename", f"{NAME}.exe"),
                            StringStruct(
                                "LegalCopyright",
                                f"© {copyright_years(date.today().year)} {AUTHOR}. PolyForm Strict License 1.0.0.",
                            ),
                        ],
                    )
                ]
            ),
            VarFileInfo([VarStruct("Translation", [0x0409, 1200])]),
        ],
    ),
)
