"""Pytest Fixtures: kleine DB, index.jsonl, Testdateien."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
import numpy as np


@pytest.fixture
def tmp_path_fixed(tmp_path):
    return tmp_path


@pytest.fixture
def sample_csv(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("1.0,2.0,3.0\n4.0,5.0,6.0\n", encoding="utf-8")
    return p


@pytest.fixture
def sample_npy(tmp_path):
    p = tmp_path / "data.npy"
    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    np.save(p, arr)
    return p


@pytest.fixture
def sample_db(tmp_path):
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE data (id INTEGER PRIMARY KEY, relpath TEXT)")
    conn.execute("INSERT INTO data (id, relpath) VALUES (1, 'data.csv'), (2, 'data.npy')")
    conn.commit()
    conn.close()
    return db


@pytest.fixture
def sample_jsonl(tmp_path):
    p = tmp_path / "index.jsonl"
    lines = [
        '{"id": 1, "relpath": "data.csv"}\n',
        '{"id": 2, "relpath": "data.npy"}\n',
    ]
    p.write_text("".join(lines), encoding="utf-8")
    return p
