"""Tests fuer scalar_stats.loaders."""
from __future__ import annotations

from pathlib import Path

import pytest
import numpy as np

from scalar_stats.loaders import load_file_as_array


def test_load_csv(sample_csv):
    arr, err = load_file_as_array(sample_csv)
    assert err is None
    assert arr is not None
    np.testing.assert_array_almost_equal(arr, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])


def test_load_npy(sample_npy):
    arr, err = load_file_as_array(sample_npy)
    assert err is None
    assert arr is not None
    np.testing.assert_array_almost_equal(arr, [1.0, 2.0, 3.0, 4.0, 5.0])


def test_load_missing_file(tmp_path):
    arr, err = load_file_as_array(tmp_path / "missing.npy")
    assert arr is None
    assert err is not None
    assert "missing" in str(err).lower()
