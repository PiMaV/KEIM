"""Tests for scalar_stats.reader."""
from __future__ import annotations

from pathlib import Path

import pytest

from scalar_stats.reader import load_db_rows, load_jsonl_rows, get_data_table_count
from scalar_stats.config import load_db_config


def test_get_data_table_count(sample_db):
    assert get_data_table_count(sample_db) == 2


def test_get_data_table_count_missing(tmp_path):
    assert get_data_table_count(tmp_path / "nonexistent.db") == 0


def test_load_db_config_missing_table(tmp_path):
    db = tmp_path / "empty.db"
    conn = __import__("sqlite3").connect(db)
    conn.execute("CREATE TABLE data (id INTEGER, relpath TEXT)")
    conn.commit()
    conn.close()
    cfg = load_db_config(db)
    assert cfg.table_name == "data"
    assert cfg.relative_filepath_column == "relpath"


def test_load_db_config_with_config_table(tmp_path):
    db = tmp_path / "with_config.db"
    conn = __import__("sqlite3").connect(db)
    conn.execute("CREATE TABLE config (key TEXT, value TEXT)")
    conn.execute("CREATE TABLE data (id INTEGER, relpath TEXT)")
    conn.execute("INSERT INTO config (key, value) VALUES ('table_name', 'data'), ('relative_filepath_column', 'relpath')")
    conn.commit()
    conn.close()
    cfg = load_db_config(db)
    assert cfg.table_name == "data"


def test_load_db_rows(sample_db, sample_csv, sample_npy, tmp_path):
    # sample_db verweist auf data.csv, data.npy relativ zu tmp_path - DB liegt in tmp_path
    rows = load_db_rows(sample_db)
    assert len(rows) == 2
    assert rows[0]["id"] == 1 and rows[0]["relpath"] == "data.csv"
    assert rows[1]["id"] == 2 and rows[1]["relpath"] == "data.npy"


def test_load_jsonl_rows(sample_jsonl, tmp_path):
    rows = load_jsonl_rows(sample_jsonl, tmp_path)
    assert len(rows) == 2
    assert rows[0]["relpath"] == "data.csv"
    assert rows[1]["relpath"] == "data.npy"
