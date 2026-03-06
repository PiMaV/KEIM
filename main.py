"""
KEIM entry: start GUI or headless CLI (--db / --index --root).
PyInstaller entry point: main.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def headless(db_path: Path | None, index_path: Path | None, root: Path | None,
             output: str, out_path: Path | None, workers: int) -> int:
    from scalar_stats.worker import run_pipeline

    def log(msg: str) -> None:
        print(msg)

    opts = {"log_callback": log}
    if db_path:
        opts["db_path"] = db_path
        opts["output_mode"] = output
        if root:
            opts["root_dir"] = root
        if output != "db" and out_path:
            opts["out_path"] = out_path
    else:
        if not index_path or not root:
            log("With --index please provide --root.")
            return 1
        opts["index_path"] = index_path
        opts["root_dir"] = root
        opts["output_mode"] = output
        opts["out_path"] = out_path or Path("keim_out.csv")
    opts["workers"] = workers
    ok, err = run_pipeline(**opts)
    log(f"Result: {ok} OK, {err} errors")
    return 0 if err == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="KEIM - Scalar statistics on linked files")
    parser.add_argument("--db", type=Path, help="SQLite database path (DAMPF contract)")
    parser.add_argument("--index", type=Path, help="index.jsonl path")
    parser.add_argument("--root", type=Path, help="Root directory (for --index or override for --db)")
    parser.add_argument("--output", choices=["db", "csv", "json"], default="db", help="Output format")
    parser.add_argument("--out-path", type=Path, help="Output file for CSV/JSON")
    parser.add_argument("--workers", type=int, default=max(1, __import__("multiprocessing").cpu_count() // 2), help="Number of workers")
    args = parser.parse_args()

    if args.db or (args.index and args.root):
        return headless(
            db_path=args.db,
            index_path=args.index,
            root=args.root,
            output=args.output,
            out_path=args.out_path,
            workers=args.workers,
        )

    # GUI
    from PySide6.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
