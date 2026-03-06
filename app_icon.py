"""
App icon helper: one 64x64 .ico, no extra sizes or artwork.
Copy this file into your project. Place icon_64.ico in an "icon" folder.
PyInstaller: add (icon/icon_64.ico, "icon") to datas, and icon="icon/icon_64.ico" in EXE.
Then call set_window_icon(main_window) in your main window.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def get_icon_path(basename: str = "icon_64.ico", relative_to: Path | None = None) -> Path | None:
    """Path to the icon file. Frozen: sys._MEIPASS/icon/<basename>. Else: relative_to/icon/<basename>."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = (relative_to or Path(__file__).resolve()).parent
    p = base / "icon" / basename
    return p if p.is_file() else None


def set_window_icon(window: "QWidget", basename: str = "icon_64.ico", relative_to: Path | None = None) -> None:
    """Set the window icon from icon/icon_64.ico (64x64). Safe to call if file is missing."""
    from PySide6.QtGui import QIcon

    p = get_icon_path(basename=basename, relative_to=relative_to)
    if p:
        window.setWindowIcon(QIcon(str(p)))
