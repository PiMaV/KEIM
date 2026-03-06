"""Tests for scalar_stats.writer."""
from __future__ import annotations

from pathlib import Path

import sqlite3
import pytest

from scalar_stats.writer import write_to_db, write_to_csv, write_to_json, STAT_COLUMNS


def test_write_to_csv(tmp_path):
    results = [
        {"id": 1, "relpath": "a.csv", "file_min": 1.0, "file_max": 2.0, "file_mean": 1.5, "file_std": 0.5, "file_median": 1.5, "file_snr": 3.0},
        {"id": 2, "relpath": "b.csv", "file_stats_error": "File missing"},
    ]
    out = tmp_path / "out.csv"
    write_to_csv(out, results)
    assert out.is_file()
    content = out.read_text(encoding="utf-8")
    assert "file_min" in content and "a.csv" in content


def test_write_to_json(tmp_path):
    results = [{"id": 1, "relpath": "a.csv", "file_min": 1.0}]
    out = tmp_path / "out.json"
    write_to_json(out, results)
    assert out.is_file()
    data = __import__("json").loads(out.read_text(encoding="utf-8"))
    assert data[0]["id"] == 1 and data[0]["file_min"] == 1.0


def test_write_to_db(sample_db, tmp_path):
    results = [
        {"id": 1, "relpath": "a.csv", "file_min": 1.0, "file_max": 2.0, "file_mean": 1.5, "file_std": 0.5, "file_median": 1.5, "file_snr": 3.0},
        {"id": 2, "relpath": "b.csv", "file_stats_error": "Error"},
    ]
    write_to_db(sample_db, results, table_name="data")
    conn = sqlite3.connect(sample_db)
    row = conn.execute("SELECT file_min, file_max, file_stats_error FROM data WHERE id IN (1, 2) ORDER BY id").fetchall()
    conn.close()
    assert row[0][0] == 1.0 and row[0][1] == 2.0
    assert row[1][2] == "Error"
