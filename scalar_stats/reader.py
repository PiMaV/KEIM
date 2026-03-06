"""
Read rows from SQLite DB or index.jsonl.
Returns list of dict with id and relpath (or configurable column name).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .config import load_db_config, DbConfig


def get_data_table_count(db_path: Path) -> int:
    """Return number of rows in the data table (for display as 'X images')."""
    db_path = Path(db_path)
    if not db_path.is_file():
        return 0
    cfg = load_db_config(db_path)
    try:
        conn = sqlite3.connect(db_path)
        n = conn.execute(f"SELECT COUNT(*) FROM [{cfg.table_name}]").fetchone()[0]
        conn.close()
        return n
    except Exception:
        return 0


def get_table_names(db_path: Path) -> list[str]:
    """Return list of table names in the DB (for diagnostics when row count is 0)."""
    db_path = Path(db_path)
    if not db_path.is_file():
        return []
    try:
        conn = sqlite3.connect(db_path)
        names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        conn.close()
        return names
    except Exception:
        return []


def get_count_from_table(db_path: Path, table_name: str) -> int:
    """Return row count for a given table (for diagnostics)."""
    db_path = Path(db_path)
    if not db_path.is_file():
        return 0
    try:
        conn = sqlite3.connect(db_path)
        n = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
        conn.close()
        return n
    except Exception:
        return -1


def get_table_columns(db_path: Path, table_name: str) -> list[str]:
    """Return column names for a table (for diagnostics)."""
    db_path = Path(db_path)
    if not db_path.is_file():
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(f"SELECT 1 FROM [{table_name}] LIMIT 0")
        cur = conn.execute(f"PRAGMA table_info([{table_name}])")
        names = [r[1] for r in cur]
        conn.close()
        return names
    except Exception:
        return []


def load_db_rows(db_path: Path, root_override: Path | None = None) -> list[dict]:
    """
    Open SQLite, load config (root_dir, table_name, relative_filepath_column).
    Read all rows from table; each row has id, relpath (or column name from config).
    root_override overrides root_dir from config.
    Return: [{"id": 1, "relpath": "exp1/run1.tif"}, ...]
    """
    db_path = Path(db_path)
    if not db_path.is_file():
        return []
    cfg = load_db_config(db_path)
    root = root_override if root_override is not None else cfg.resolve_root(db_path)
    cfg.root_dir = root
    table = cfg.table_name
    rel_col = cfg.relative_filepath_column
    rows = []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(f"SELECT id, [{rel_col}] FROM [{table}]")
        for r in cur:
            raw = r[rel_col]
            relpath = (raw.strip() if raw else "") or ""
            rows.append({
                "id": r["id"],
                "relpath": relpath,
            })
        conn.close()
    except Exception:
        return []
    return rows


def load_jsonl_rows(index_path: Path, root: Path) -> list[dict]:
    """
    Read JSONL line by line; each line has 'relpath' or 'path'.
    Id optional (line number as id).
    """
    index_path = Path(index_path)
    root = Path(root)
    if not index_path.is_file():
        return []
    rows = []
    with open(index_path, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            relpath = obj.get("relpath") or obj.get("path") or ""
            rows.append({"id": obj.get("id", i), "relpath": relpath})
    return rows
