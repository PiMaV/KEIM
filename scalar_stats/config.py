"""
Config for DB input: table name, relpath column, root directory.
Read from DB config table or use defaults.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from dataclasses import dataclass


DEFAULT_TABLE_NAME = "data"
DEFAULT_RELPATH_COLUMN = "relpath"
CONFIG_TABLE = "config"


@dataclass
class DbConfig:
    """Table name, relpath column, root directory (from DB or caller)."""
    table_name: str = DEFAULT_TABLE_NAME
    relative_filepath_column: str = DEFAULT_RELPATH_COLUMN
    root_dir: Path | None = None

    def resolve_root(self, db_path: Path) -> Path:
        """Root directory: configured root_dir or DB file's directory."""
        if self.root_dir is not None and self.root_dir.is_dir():
            return self.root_dir.resolve()
        return db_path.resolve().parent


def load_db_config(db_path: Path) -> DbConfig:
    """
    Read config from SQLite: table 'config' with key/value.
    Validate table/column exist; fall back to defaults if not.
    """
    cfg = DbConfig()
    db_path = Path(db_path)
    if not db_path.is_file():
        return cfg
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT key, value FROM config WHERE key IN ('root_dir', 'table_name', 'relative_filepath_column')"
        )
        for row in cur:
            k = (row["key"] or "").strip().lower()
            v = (row["value"] or "").strip()
            if k == "root_dir" and v:
                cfg.root_dir = Path(v)
            elif k == "table_name" and v:
                cfg.table_name = v
            elif k == "relative_filepath_column" and v:
                cfg.relative_filepath_column = v
        # Validate: table must exist and column must exist
        try:
            cur = conn.execute(f"PRAGMA table_info([{cfg.table_name}])")
            cols = [r[1] for r in cur]
        except Exception:
            cols = []
        if not cols or cfg.relative_filepath_column not in cols:
            cfg.table_name = DEFAULT_TABLE_NAME
            cfg.relative_filepath_column = DEFAULT_RELPATH_COLUMN
        conn.close()
    except (sqlite3.OperationalError, Exception):
        pass
    return cfg
