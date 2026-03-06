"""
Unified interface for picture-like data: path -> 1D or 2D numpy array.
- Images: max 3D (H, W) or (H, W, C); third dimension = color channels. Reduced to 2D intensity for metrics.
- CSV/TSV: rows and columns of numeric values -> 2D matrix (lines x columns).
On error: None + error message.
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np

try:
    import tifffile
except ImportError:
    tifffile = None
try:
    from PIL import Image
except ImportError:
    Image = None
try:
    import h5py
except ImportError:
    h5py = None

IMAGE_EXT = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}
CSV_EXT = {".csv", ".tsv"}
NPY_EXT = {".npy", ".npz"}
H5_EXT = {".h5", ".hdf5"}


def load_file_as_array(path: Path) -> Tuple[np.ndarray | None, str | None]:
    """Load file as 1D array. Return (array, None) on success, (None, error_message) on error."""
    path = Path(path)
    if not path.exists():
        return None, f"File missing: {path}"
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXT:
        return _load_image(path)
    if suffix in CSV_EXT:
        return _load_csv_tsv(path)
    if suffix == ".npy":
        return _load_npy(path)
    if suffix == ".npz":
        return _load_npz(path)
    if suffix in H5_EXT:
        return _load_h5(path)
    return None, f"Nicht unterstuetzter Dateityp: {suffix}"


def _load_image(path: Path) -> Tuple[np.ndarray | None, str | None]:
    arr_2d, err = load_image_2d(path)
    if err or arr_2d is None:
        return (None, err) if err else (None, "Unsupported image")
    return np.asarray(arr_2d).flatten(), None


def _image_to_2d(arr: np.ndarray) -> np.ndarray:
    """Reduce image to 2D: (H,W) unchanged, (H,W,C) -> mean over channels."""
    arr = np.asarray(arr, dtype=float)
    if arr.ndim == 2:
        return arr
    if arr.ndim == 3:
        return arr.mean(axis=-1)
    return arr.reshape(-1, arr.shape[-2], arr.shape[-1])[0]


def load_image_2d(path: Path) -> Tuple[np.ndarray | None, str | None]:
    """Load image as 2D array (max 3D on disk: H,W or H,W,C; C reduced to intensity). For coverage/bbox."""
    path = Path(path)
    if not path.exists():
        return None, f"File missing: {path}"
    if path.suffix.lower() not in IMAGE_EXT:
        return None, f"Not an image: {path.suffix}"
    ext = path.suffix.lower()
    if ext in {".tif", ".tiff"} and tifffile is not None:
        try:
            arr = tifffile.imread(path)
            return _image_to_2d(arr), None
        except Exception as e:
            return None, str(e)
    if Image is not None:
        try:
            img = Image.open(path)
            arr = np.array(img)
            return _image_to_2d(arr), None
        except Exception as e:
            return None, str(e)
    return None, "tifffile or Pillow required for image files"


def load_csv_2d(path: Path) -> Tuple[np.ndarray | None, str | None]:
    """Load CSV/TSV as 2D matrix (lines x columns of numeric values). Returns (array, None) or (None, error)."""
    path = Path(path)
    if not path.exists():
        return None, f"File missing: {path}"
    if path.suffix.lower() not in CSV_EXT:
        return None, f"Not CSV/TSV: {path.suffix}"
    try:
        import csv
        delim = "\t" if path.suffix.lower() == ".tsv" else ","
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=delim)
            rows = list(reader)
        if not rows:
            return None, "Empty file"
        parsed = []
        for row in rows:
            line = []
            for cell in row:
                try:
                    line.append(float(cell))
                except ValueError:
                    pass
            if line:
                parsed.append(line)
        if not parsed:
            return None, "No numeric values found"
        n_cols = min(len(r) for r in parsed)
        if n_cols == 0:
            return None, "No numeric values found"
        arr = np.array([r[:n_cols] for r in parsed], dtype=float)
        return arr, None
    except Exception as e:
        return None, str(e)


def _load_csv_tsv(path: Path) -> Tuple[np.ndarray | None, str | None]:
    """Load CSV/TSV as 1D array (flattened 2D matrix) for scalar stats."""
    arr_2d, err = load_csv_2d(path)
    if err or arr_2d is None:
        return (None, err) if err else (None, "Empty CSV/TSV")
    return np.asarray(arr_2d).flatten(), None


def _load_npy(path: Path) -> Tuple[np.ndarray | None, str | None]:
    try:
        arr = np.load(path)
        return np.asarray(arr).flatten(), None
    except Exception as e:
        return None, str(e)


def _load_npz(path: Path) -> Tuple[np.ndarray | None, str | None]:
    try:
        with np.load(path) as z:
            keys = list(z.keys())
            if not keys:
                return None, "Empty npz"
            arr = z[keys[0]]
        return np.asarray(arr).flatten(), None
    except Exception as e:
        return None, str(e)


def _load_h5(path: Path) -> Tuple[np.ndarray | None, str | None]:
    if h5py is None:
        return None, "h5py required for .h5/.hdf5"
    try:
        with h5py.File(path, "r") as f:
            def first_dataset(obj):
                if hasattr(obj, "keys"):
                    for k in obj.keys():
                        child = obj[k]
                        if isinstance(child, h5py.Dataset):
                            return np.asarray(child).flatten()
                        res = first_dataset(child)
                        if res is not None:
                            return res
                return None
            arr = first_dataset(f)
        if arr is None:
            return None, "No dataset found in h5 file"
        return arr, None
    except Exception as e:
        return None, str(e)
