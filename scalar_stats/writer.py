"""
Output: extend DB (ALTER TABLE, UPDATE) or write CSV/JSON.
Error rows: NULL or file_stats_error column in DB; in CSV/JSON a row with error message.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from . import stats

STAT_COLUMNS = stats.ALL_STAT_KEYS
ERROR_COLUMN = "file_stats_error"


def write_to_db(
    db_path: Path,
    results: list[dict],
    table_name: str = "data",
    stat_columns: tuple[str, ...] | None = None,
) -> None:
    """
    Extend table with stat columns (ADD COLUMN if missing), then UPDATE per id.
    If stat_columns is given, only those columns are added/updated; else all STAT_COLUMNS.
    """
    cols = stat_columns if stat_columns is not None and len(stat_columns) else STAT_COLUMNS
    db_path = Path(db_path)
    conn = sqlite3.connect(db_path)
    for col in cols:
        try:
            conn.execute(f"ALTER TABLE [{table_name}] ADD COLUMN [{col}] REAL")
        except sqlite3.OperationalError:
            pass
    try:
        conn.execute(f"ALTER TABLE [{table_name}] ADD COLUMN [{ERROR_COLUMN}] TEXT")
    except sqlite3.OperationalError:
        pass
    placeholders = ", ".join(f"[{c}] = ?" for c in cols)
    for r in results:
        row_id = r.get("id")
        err = r.get("file_stats_error")
        if err:
            conn.execute(
                f"UPDATE [{table_name}] SET [{ERROR_COLUMN}] = ? WHERE id = ?",
                (err, row_id),
            )
            continue
        vals = [r.get(c) for c in cols]
        conn.execute(
            f"UPDATE [{table_name}] SET {placeholders} WHERE id = ?",
            vals + [row_id],
        )
    conn.commit()
    conn.close()


def write_to_csv(out_path: Path, results: list[dict], stat_columns: tuple[str, ...] | None = None) -> None:
    """Write CSV with id, relpath, selected stat columns, file_stats_error."""
    out_path = Path(out_path)
    stat_cols = stat_columns if stat_columns else STAT_COLUMNS
    cols = ["id", "relpath"] + list(stat_cols) + [ERROR_COLUMN]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(f'"{c}"' for c in cols) + "\n")
        for r in results:
            row = [str(r.get(c, "")) for c in cols]
            f.write(",".join(f'"{_escape(v)}"' for v in row) + "\n")


def _escape(s: Any) -> str:
    return str(s).replace('"', '""')


def write_to_json(out_path: Path, results: list[dict], stat_columns: tuple[str, ...] | None = None) -> None:
    """Write JSON list of objects with id, relpath, selected stats, file_stats_error."""
    out_path = Path(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
