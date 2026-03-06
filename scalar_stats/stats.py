"""
Scalar statistics from 1D array: min, max, mean, std, median, SNR.
Uses np.nanmin etc.; SNR = mean/std (std > 0), else nan.
"""
from __future__ import annotations

import numpy as np

ALL_STAT_KEYS = ("file_min", "file_max", "file_mean", "file_std", "file_median", "file_snr")


def compute_scalar_stats(arr: np.ndarray, stats_keys: list[str] | None = None) -> dict[str, float]:
    """
    Compute min, max, mean, std, median, snr (mean/std).
    If stats_keys is given, only those keys are returned (e.g. ["file_min", "file_max"]).
    """
    arr = np.asarray(arr).flatten()
    arr = np.asarray(arr, dtype=float)
    if arr.size == 0:
        full = {k: float("nan") for k in ALL_STAT_KEYS}
        return _filter_stats(full, stats_keys)
    nanmin = np.nanmin(arr)
    nanmax = np.nanmax(arr)
    nanmean = np.nanmean(arr)
    nanstd = np.nanstd(arr)
    nanmedian = np.nanmedian(arr)
    if nanstd is not None and nanstd > 0:
        snr = float(nanmean / nanstd)
    else:
        snr = float("nan")
    full = {
        "file_min": float(nanmin),
        "file_max": float(nanmax),
        "file_mean": float(nanmean),
        "file_std": float(nanstd) if not np.isnan(nanstd) else float("nan"),
        "file_median": float(nanmedian),
        "file_snr": snr,
    }
    return _filter_stats(full, stats_keys)


def _filter_stats(full: dict[str, float], stats_keys: list[str] | None) -> dict[str, float]:
    if stats_keys is None:
        return full
    return {k: full[k] for k in stats_keys if k in full}
