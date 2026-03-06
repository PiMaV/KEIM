"""
Pipeline: reader -> loaders+stats (parallel) -> writer.
Callbacks for progress and log (GUI/headless).
"""
from __future__ import annotations

from pathlib import Path
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import reader, loaders, stats, writer
from .config import load_db_config


def _process_one(row: dict, root: Path, stats_keys: list[str] | None = None) -> dict:
    """Resolve path, load file, compute selected stats."""
    relpath = (row.get("relpath") or "").strip()
    # Normalize slashes so "a/b" joins correctly on Windows
    parts = relpath.replace("\\", "/").split("/")
    abs_path = (root / Path(*parts)).resolve()
    arr, err = loaders.load_file_as_array(abs_path)
    out = {"id": row["id"], "relpath": relpath}
    if err:
        out["file_stats_error"] = err
        return out
    out.update(stats.compute_scalar_stats(arr, stats_keys=stats_keys))
    return out


def run_pipeline(
    *,
    db_path: Path | None = None,
    index_path: Path | None = None,
    root_dir: Path | None = None,
    output_mode: str = "db",
    out_path: Path | None = None,
    workers: int | None = None,
    stats_keys: list[str] | None = None,
    progress_callback: callable | None = None,
    log_callback: callable | None = None,
) -> tuple[int, int]:
    """
    Run full pipeline. Either db_path (SQLite) OR index_path + root_dir (JSONL).
    output_mode: "db" | "csv" | "json". out_path required for csv/json.
    stats_keys: list of keys to compute (e.g. ["file_min", "file_max"]); None = all.
    """
    def log(msg: str) -> None:
        if log_callback:
            log_callback(msg)

    if db_path and db_path.is_file():
        log(f"Loading database: {db_path}")
        cfg = load_db_config(db_path)
        # Root: explicit override, else root_dir from config table, else DB file's directory
        root = root_dir if root_dir is not None else cfg.resolve_root(db_path)
        log(f"Root for images (from config or DB dir): {root}")
        rows = reader.load_db_rows(db_path, root_override=root_dir)
        table_name = cfg.table_name
    elif index_path and index_path.is_file() and root_dir is not None:
        root = Path(root_dir)
        log(f"Loading index: {index_path}")
        log(f"Root for images: {root}")
        rows = reader.load_jsonl_rows(index_path, root)
        table_name = "data"
    else:
        log("Error: provide db_path or index_path + root_dir.")
        return 0, 0

    if not rows:
        log("No rows to process.")
        return 0, 0

    total = len(rows)
    num_workers = workers if workers is not None and workers >= 1 else max(1, multiprocessing.cpu_count() // 2)
    stat_cols = tuple(stats_keys) if stats_keys else None
    # Diagnostic: where we look for the first file
    first_rel = (rows[0].get("relpath") or "").strip()
    if first_rel:
        parts = first_rel.replace("\\", "/").split("/")
        first_abs = (root / Path(*parts)).resolve()
        log(f"Searching for images under root. First file: {first_abs}")
    log(f"Processing {total} entries, workers: {num_workers}")

    results = [None] * len(rows)
    success = 0
    errors = 0
    completed = 0
    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        future_to_idx = {
            pool.submit(_process_one, row, root, stats_keys): i
            for i, row in enumerate(rows)
        }
        for future in as_completed(future_to_idx):
            i = future_to_idx[future]
            try:
                out = future.result()
                results[i] = out
                if out.get("file_stats_error"):
                    errors += 1
                    log(f"Error [{out['id']}] {out.get('relpath', '')}: {out['file_stats_error']}")
                else:
                    success += 1
            except Exception as e:
                results[i] = {"id": rows[i]["id"], "relpath": rows[i].get("relpath", ""), "file_stats_error": str(e)}
                errors += 1
                log(f"Error [{rows[i]['id']}]: {e}")
            completed += 1
            if progress_callback:
                progress_callback(completed, total, f"Processed {completed}/{total}")
    results = [r for r in results if r is not None]

    if output_mode == "db" and db_path:
        writer.write_to_db(db_path, results, table_name=table_name, stat_columns=stat_cols)
        log(f"DB updated: {db_path}")
    elif output_mode == "csv" and out_path:
        writer.write_to_csv(out_path, results, stat_columns=stat_cols)
        log(f"CSV written: {out_path}")
    elif output_mode == "json" and out_path:
        writer.write_to_json(out_path, results, stat_columns=stat_cols)
        log(f"JSON written: {out_path}")
    else:
        log("Output not written (output_mode/out_path?).")

    log(f"Done: {success} OK, {errors} errors")
    return success, errors
