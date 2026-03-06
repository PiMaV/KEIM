"""
Scalar statistics from 1D array: min, max, mean, std, median, SNR.
Image-only: content_pct (threshold + % above), bbox_area_pct (% of image covered by content bbox).
"""
from __future__ import annotations

import numpy as np

ALL_STAT_KEYS = (
    "file_min", "file_max", "file_mean", "file_std", "file_median", "file_snr",
    "file_content_pct", "file_bbox_area_pct",
)
IMAGE_ONLY_KEYS = ("file_content_pct", "file_bbox_area_pct")


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


def compute_image_coverage(
    arr_2d: np.ndarray,
    threshold: str = "mean",
    stats_keys: list[str] | None = None,
) -> dict[str, float]:
    """
    Threshold image, build content mask, return fraction of pixels above threshold (content %)
    and fraction of image area covered by the content bounding box.
    threshold: "mean" or "median" (relative to image values).
    """
    arr_2d = np.asarray(arr_2d, dtype=float)
    if arr_2d.ndim != 2 or arr_2d.size == 0:
        out = {"file_content_pct": float("nan"), "file_bbox_area_pct": float("nan")}
        return _filter_stats(out, stats_keys)
    th = np.nanmean(arr_2d) if threshold == "mean" else np.nanmedian(arr_2d)
    if np.isnan(th):
        out = {"file_content_pct": float("nan"), "file_bbox_area_pct": float("nan")}
        return _filter_stats(out, stats_keys)
    mask = arr_2d > th
    total = arr_2d.size
    content_pct = float(mask.sum() / total) if total else float("nan")
    rows, cols = np.where(mask)
    if len(rows) == 0:
        bbox_area_pct = 0.0
    else:
        rmin, rmax = int(rows.min()), int(rows.max())
        cmin, cmax = int(cols.min()), int(cols.max())
        bbox_area = (rmax - rmin + 1) * (cmax - cmin + 1)
        bbox_area_pct = float(bbox_area / total)
    out = {"file_content_pct": content_pct, "file_bbox_area_pct": bbox_area_pct}
    return _filter_stats(out, stats_keys)
