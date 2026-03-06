# KEIM - Knowledge Extraction & Indexing Module

Eigenstaendiges Programm (GUI) fuer Skalarstatistiken auf verknuepften Dateien: nach DAMPF-Indexlauf werden Dateiinhalte (Bilder, Matrizen) geladen und min, max, mean, std, median, SNR berechnet. Ausgabe in DB-Erweiterung oder CSV/JSON.

## Anforderungen

- Python 3.10+
- Abhaengigkeiten: `pip install -r requirements.txt`

## Nutzung (GUI)

1. Programm starten: `python main.py`
2. **Eingabe:** Entweder SQLite-DB waehlen (Durchsuchen oder DB-Datei per Drag & Drop) oder index.jsonl + Root-Verzeichnis.
3. Optional: Root-Override, Ausgabe (DB erweitern / CSV / JSON), Ausgabepfad, Workers (Default: CPU-Anzahl/2).
4. **Starten** klicken; Fortschritt und Log erscheinen im Fenster.

## Headless (z.B. DAMPF-Button)

Die gebaute .exe (bzw. das Linux-Binary) kann mit Argumenten aufgerufen werden – dann startet keine GUI, die Pipeline laeuft mit Log auf stdout:

```text
keim.exe --db Pfad/zur/datenbank.db
keim.exe --db Pfad/zur/datenbank.db --root /anderes/root --output csv --out-path out.csv
keim.exe --index index.jsonl --root /path/to/root --output csv --out-path out.csv --workers 4
```

## Build mit PyInstaller (.exe / Ubuntu)

### Mit uv (empfohlen, gekapselt)

Build in einer isolierten Umgebung – nur KEIM-Abhaengigkeiten, kein globales PyQt/matplotlib/pytest. [uv](https://github.com/astral-sh/uv) installieren, dann im Projektverzeichnis:

```bash
uv sync --extra dev
uv run pyinstaller build.spec
```

Fertige Datei: `dist/keim.exe` (Windows) bzw. `dist/keim` (Linux). Optional: `uv lock` vor dem ersten Build. Falls `uv sync` scheitert (z.B. fehlendes build-backend): `uv venv` → `uv pip install -r requirements.txt pyinstaller` → `uv run pyinstaller build.spec`.

### Ohne uv (pip)

- PyInstaller installieren: `pip install pyinstaller`
- Im Projektverzeichnis (KEIM):  
  `pyinstaller build.spec`
- **Windows:** `dist/keim.exe` (one-file, Icon: `icon/icon_64.ico`)
- **Ubuntu/Linux:** Auf Linux/WSL denselben Befehl → `dist/keim`

Hinweis: Windows-.exe unter Windows bauen, Linux-Binary unter Linux – plattformuebergreifendes Bauen wird nicht unterstuetzt.

**Groesse:** Die .exe liegt typisch bei ca. 65 MB (PySide6/Qt6 + numpy + PIL + h5py). Unbenutzte Pakete (matplotlib, pytest, IPython, etc.) sind in der Spec ausgeschlossen. Eine tkinter-GUI waere deutlich schlanker (ca. 20–35 MB), da tkinter zur Python-Standardbibliothek gehoert; dafuer muesste die GUI von PySide6 auf tkinter umgestellt werden. Qt gibt es nicht in einer schlankeren Variante – PySide2 (Qt5) ist nur wenig kleiner als PySide6.

## Optionale DAMPF-Anbindung

In DAMPF kann ein Button „Skalarstats berechnen“ die fertige KEIM-.exe aufrufen, z.B.:

`keim.exe --db <DB-Pfad aus dem DAMPF-Dialog>`

Die Ausgabe erscheint in der Konsole bzw. kann von DAMPF aus gelesen werden (z.B. Subprocess mit stdout/stderr ins Log).

## Tests

Aus dem Projektverzeichnis: `python -m pytest tests/`

## Icon (Exe + Fenster)

- **app_icon.py** – wiederverwendbar: in andere Projekte kopieren, `icon/icon_64.ico` ablegen, `set_window_icon(fenster)` aufrufen.
- **icon/icon_64.ico** – eine .ico mit **mehreren Groessen (16, 32, 48, 64, 128, 256)**. Windows zeigt das Exe-Icon im Explorer nur, wenn die .ico mehrere Groessen enthaelt; eine einzige 64x64 reicht dafuer oft nicht.
- Erzeugen: `icon_256.png` (oder `icon_64.png`) in `icon/` legen, dann `uv run python icon/build_ico.py`. Das Skript schreibt `icon_64.ico` mit allen Groessen.

### Auf andere Programme anwenden (z.B. DAMPF)

1. **Icon-Ordner:** Im Projekt z.B. `icon/` mit mindestens einer PNG (z.B. `icon_64.png` oder `icon_256.png`).
2. **build_ico.py** aus KEIM kopieren nach `icon/build_ico.py`, einmal ausfuehren → `icon/icon_64.ico` mit 16..256 px.
3. **app_icon.py** aus KEIM ins Projektroot kopieren. Im Hauptfenster: `set_window_icon(self, "icon_64.ico", relative_to=Path(__file__).resolve().parent.parent)` (oder passenden Pfad).
4. **PyInstaller-Spec:** Icon fuer die Exe setzen und in datas packen:
   - `_icon_64_ico = os.path.join(SPECPATH, 'icon', 'icon_64.ico')`
   - `datas` um `[(_icon_64_ico, 'icon')]` erweitern
   - `EXE(..., icon=_icon_64_ico)`
5. Exe neu bauen. Falls Explorer das Icon nicht zeigt: Icon-Cache leeren (Explorer neu starten / Rechner neu starten) oder sicherstellen, dass die .ico wirklich 16/32/48/64/128/256 enthaelt.

## Projektstruktur

- `main.py` – Einstieg (GUI oder Headless)
- `app_icon.py` – Icon-Helfer (eine 64px-.ico; in andere Projekte kopierbar)
- `scalar_stats/` – reader, loaders, stats, writer, config, worker
- `gui/` – Hauptfenster (PySide6)
- `icon/icon_64.ico` – einziges Icon (64x64)
- `build.spec` – PyInstaller-Spec fuer keim.exe / keim (Linux)
