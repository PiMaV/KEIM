# KEIM — Knowledge Extraction & Inference Module

Scalar statistics on linked files after a **DAMPF** index run: load images and matrices, compute min, max, mean, std, median, and SNR, then write results back into the SQLite database (or CSV/JSON).

**WETTER pipeline:** `Raw Data → DAMPF → KEIM → WOLKE → BLITZ`

Overview and module links: **[wetter.mess.engineering](https://wetter.mess.engineering)**

[Download the latest release](https://github.com/PiMaV/KEIM/releases/latest) (Windows `.exe` and Linux binary).

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`

## Install and run

```bash
git clone https://github.com/PiMaV/KEIM.git
cd KEIM
uv sync
uv run python main.py
```

Without uv: `pip install -r requirements.txt`, then `python main.py` in a virtualenv.

**GUI:** choose a SQLite DB (browse or drag-and-drop) or `index.jsonl` plus a root directory. Optionally override the root, pick output (extend DB / CSV / JSON), set workers (default: CPU count / 2), then start. Progress and log appear in the window.

## Headless (e.g. from DAMPF)

With arguments there is no GUI; the pipeline logs to stdout:

```text
keim.exe --db path/to/database.db
keim.exe --db path/to/database.db --root /other/root --output csv --out-path out.csv
keim.exe --index index.jsonl --root /path/to/root --output csv --out-path out.csv --workers 4
```

From source: `uv run python main.py --db path/to/database.db`

DAMPF can call the built binary, for example `keim.exe --db <DB path from the DAMPF dialog>`.

## Tests

```bash
uv sync --extra dev
uv run pytest
```

Without uv: `python -m pytest tests/`

## Build a standalone binary

```bash
uv sync --extra dev
uv run pyinstaller build.spec
```

Output: `dist/keim.exe` (Windows) or `dist/keim` (Linux). Build on the target OS. Tag `v*` on GitHub publishes `keim.exe` and `keim-linux-x86_64`.

Typical size is about 65 MB (PySide6 + numpy + Pillow + h5py).

## Icon (exe + window)

`icon/icon_64.ico` is a multi-size ICO (16–256 px) so Windows Explorer shows the exe icon. Rebuild with `uv run python icon/build_ico.py` from a PNG in `icon/`. `app_icon.py` sets the window icon.

## License

GNU GPL v3. See [LICENSE](LICENSE).
