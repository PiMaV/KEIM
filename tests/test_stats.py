"""Tests fuer scalar_stats.stats."""
from __future__ import annotations

import numpy as np
import pytest

from scalar_stats.stats import compute_scalar_stats


def test_compute_scalar_stats():
    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    out = compute_scalar_stats(arr)
    assert out["file_min"] == 1.0
    assert out["file_max"] == 5.0
    assert out["file_mean"] == 3.0
    assert out["file_std"] == pytest.approx(1.414, abs=0.01)
    assert out["file_snr"] == pytest.approx(3.0 / 1.414, abs=0.01)


def test_compute_scalar_stats_empty():
    out = compute_scalar_stats(np.array([]))
    assert np.isnan(out["file_min"])
    assert np.isnan(out["file_snr"])


def test_compute_scalar_stats_selected_keys():
    arr = np.array([1.0, 2.0, 3.0])
    out = compute_scalar_stats(arr, stats_keys=["file_min", "file_max"])
    assert set(out.keys()) == {"file_min", "file_max"}
    assert out["file_min"] == 1.0
    assert out["file_max"] == 3.0
