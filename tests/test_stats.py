"""Tests fuer scalar_stats.stats."""
from __future__ import annotations

import numpy as np
import pytest

from scalar_stats.stats import compute_scalar_stats, compute_image_coverage


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


def test_compute_image_coverage():
    # 3x3: center pixel 1, rest 0 -> mean 1/9; only center above threshold
    arr = np.zeros((3, 3))
    arr[1, 1] = 1.0
    out = compute_image_coverage(arr, threshold="mean")
    assert out["file_content_pct"] == pytest.approx(1.0 / 9.0)
    assert out["file_bbox_area_pct"] == pytest.approx(1.0 / 9.0)


def test_compute_image_coverage_half_filled():
    # 2x2: two 1s, two 0s -> mean 0.5; mask = pixels > 0.5 -> two 1s
    arr = np.array([[0.0, 1.0], [1.0, 0.0]])
    out = compute_image_coverage(arr, threshold="mean")
    assert out["file_content_pct"] == 0.5
    # bbox of the two 1s: rows 0,1 cols 0,1 -> area 4/4 = 1.0
    assert out["file_bbox_area_pct"] == 1.0
