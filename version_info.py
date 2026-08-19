"""
App name and version from pyproject.toml (single source of truth).
Works when run from source or from PyInstaller bundle (pyproject.toml in datas).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def _find_pyproject() -> Path | None:
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parent
    p = base / "pyproject.toml"
    return p if p.is_file() else None


def get_version() -> str:
    path = _find_pyproject()
    if not path:
        return "0.0.0"
    try:
        text = path.read_text(encoding="utf-8")
        m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', text)
        return m.group(1) if m else "0.0.0"
    except Exception:
        return "0.0.0"


APP_NAME = "Knowledge Extraction and Inference Module"


def window_title() -> str:
    return f"{APP_NAME}  v{get_version()}"
