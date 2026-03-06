"""
Unified interface: path -> 1D numpy array.
Dispatch by extension: images (tifffile/PIL), CSV/TSV, npy, npz, h5/hdf5.
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
    ext = path.suffix.lower()
    if ext in {".tif", ".tiff"} and tifffile is not None:
        try:
            arr = tifffile.imread(path)
            return np.asarray(arr).flatten(), None
        except Exception as e:
            return None, str(e)
    if Image is not None:
        try:
            img = Image.open(path)
            arr = np.array(img)
            return np.asarray(arr).flatten(), None
        except Exception as e:
            return None, str(e)
    return None, "tifffile or Pillow required for image files"


def _load_csv_tsv(path: Path) -> Tuple[np.ndarray | None, str | None]:
    try:
        import csv
        delim = "\t" if path.suffix.lower() == ".tsv" else ","
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=delim)
            rows = list(reader)
        if not rows:
            return None, "Empty file"
        values = []
        for row in rows:
            for cell in row:
                try:
                    values.append(float(cell))
                except ValueError:
                    pass
        if not values:
            return None, "No numeric values found"
        return np.array(values, dtype=float), None
    except Exception as e:
        return None, str(e)


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
