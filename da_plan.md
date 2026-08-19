# Plan: Eigenstaendiges Programm fuer Skalarstatistiken auf verknuepften Dateien

**Ziel:** Ein separates Programm (GUI), das nach dem DAMPF-Indexlauf die **Inhalte** der verknuepften Dateien (Bilder, Matrizen) laedt und skalare Statistiken berechnet (min, max, mean, std, SNR etc.). Ausgabe in DB-Erweiterung. Optional spaeter von DAMPF per Button startbar.

**Kontext:** DAMPF schreibt eine SQLite-DB mit einer Tabelle: `id`, `relpath` (Pfad relativ zum DB-Verzeichnis), plus indexierte Felder. Die Dateien liegen relativ zum DB-Ordner (oder konfigurierbarem Root). Dieses Programm liest die DB (oder index.jsonl), loest `relpath` auf, laedt jede Datei, berechnet Statistiken und schreibt das Ergebnis.

**Name:** KEIM - (Knowledge Extraction & Inference Module)

---

## 1. Anforderungen (kurz)

- **Eingabe:** SQLite-DB-Pfad (DAMPF-Contract) ODER index.jsonl + root_dir. Root-Verzeichnis = DB-Verzeichnis oder explizit angegeben.
- **Unterstuetzte Dateitypen:** Bilder (.tif, .tiff, .png, .jpg, .jpeg, .bmp), Matrizen (.csv, .tsv, .npy, .npz, .h5/.hdf5). Pro Datei: numerische Werte als 1D-Array (Bilder: flatten; CSV: alle numerischen Spalten oder erste Spalte konfigurierbar).
- **Statistiken:** min, max, mean, std, median; darauf aufbauend SNR (z.B. mean/std, konfigurierbar). erwetierbar!
- **Ausgabe:** Entweder neue Spalten in der bestehenden DB-Tabelle (z.B. `file_min`, `file_max`, `file_mean`, `file_std`, `file_snr`)
- **Robustheit:** Fehlende/defekte Dateien: Eintrag ueberspringen, in Log/Report vermerken; Ergebnis-Spalten NULL oder in separatem Report „errors“.
- **Performance:** Parallelisierung (z.B. ProcessPool oder ThreadPool) pro Datei; Fortschrittsanzeige (CLI: progress bar oder Zeilen-Log).
- **Keine Umlaute in Code/Kommentaren:** oe, ae, ue, ss (ASCII).

---

## 2. Empfohlene Projektstruktur

**eigenes Projekt** (z.B. `KEIM`):

```
scalar_stats/
  __init__.py
  cli.py
  reader.py
  loaders.py
  stats.py
  writer.py
  config.py
keim.py       # oder python -m scalar_stats
requirements.txt          # numpy, tifffile, pillow, h5py, pandas (optional)
README.md                 # Nutzung mit DAMPF-DB
```

---

## 3. Datenfluss

```
[SQLite DB oder index.jsonl] + root_dir
    -> reader: Liste {id?, relpath} (relpath aus data-Relpath-Spalte)
    -> pro relpath: root_dir / relpath -> abs_path
    -> loaders: abs_path -> np.ndarray (1D), bei Fehler None + Fehlermeldung
    -> stats: array -> {min, max, mean, std, snr}
    -> writer: Ergebnisse in DB (neue Spalten) oder CSV/JSON
```

- **DB-Fall:** Aus config-Tabelle `root_dir` lesen falls vorhanden, sonst DB-Verzeichnis als Root. Tabelle aus config (table_name) bzw. Default "data"; Relpath-Spalte aus config (relative_filepath_column) bzw. "relpath".
- **JSONL-Fall:** `--index index.jsonl --root /path/to/root`; jede Zeile hat "path" oder "relpath", Root explizit.

---

## 4. Module im Detail

### 4.1 reader.py

- `load_db_rows(db_path: Path, root_override: Path | None) -> list[dict]`
  - SQLite oeffnen, config laden (root_dir, table_name, relative_filepath_column).
  - Alle Zeilen aus Tabelle lesen; pro Zeile mindestens `id`, `relpath` (oder Spaltenname aus config). Optional root_dir aus config; wenn root_override, diesen nutzen.
  - Return: `[{"id": 1, "relpath": "exp1/run1.tif"}, ...]`
- `load_jsonl_rows(index_path: Path, root: Path) -> list[dict]`
  - JSONL zeilenweise lesen; "relpath" oder "path" (dann relativ zu root machen oder so belassen). Id optional (Zeilennummer als id).

### 4.2 loaders.py

- Einheitliche Schnittstelle: `load_file_as_array(path: Path) -> np.ndarray | None` (+ optional Fehler-Info).
- Nach Extension dispatchen:
  - **.tif, .tiff, .png, .jpg, .jpeg, .bmp:** tifffile/PIL -> numpy array, dann `.flatten()`. Bei Mehrkanal: ganzes Array flatten (oder Option „pro Kanal“ spaeter).
  - **.csv, .tsv:** Alle numerischen Spalten zu einem 1D-Array (z.B. Werte flachen); oder erste Spalte; konfigurierbar.
  - **.npy:** `np.load()` -> flatten.
  - **.npz:** Konvention: erstes Array oder festes Key (z.B. "arr_0"); flatten.
  - **.h5, .hdf5:** Konvention: erstes Dataset oder festes Key; flatten.
- Bei Fehler (Datei fehlt, Format fehlerhaft): None zurueckgeben, Fehlermeldung in Log/Queue fuer Report.

### 4.3 stats.py

- `compute_scalar_stats(arr: np.ndarray) -> dict`
  - min, max, mean, std (np.nanmin etc. fuer Robustheit).
  - Optional: median.
  - SNR: z.B. `mean / std` wenn std > 0, sonst np.nan oder 0; oder andere Definition (konfigurierbar).
  - Return: `{"file_min": float, "file_max": float, "file_mean": float, "file_std": float, "file_snr": float, ...}`

### 4.4 writer.py

- **DB-Erweiterung:** Bestehende Tabelle um Spalten erweitern (ALTER TABLE ADD COLUMN falls nicht vorhanden), dann UPDATE pro id mit den Stat-Werten. Fehlerzeilen: Spalten NULL oder eine Spalte `file_stats_error` (TEXT).
- **CSV/JSON:** Neue Datei mit id, relpath, file_min, file_max, file_mean, file_std, file_snr; bei Fehlern eigene Zeile mit id/relpath und error-Message oder leere Werte.

### 4.5 cli.py

- Argumente (Beispiel):
  - `--db PATH` (SQLite) ODER `--index PATH --root PATH` (JSONL).
  - `--root PATH` (optional, ueberschreibt DB-Root).
  - `--output (db|csv|json)` (Default: db bei DB-Eingabe, sonst csv).
  - `--out-path PATH` (fuer CSV/JSON Ausgabedatei).
  - `--workers N` (Parallelisierung, Default z.B. 4 oder cpu_count-1).
  - `--stats min,max,mean,std,snr` (optional, Default alle).
- Ablauf: reader -> pro Zeile in Pool loaders+stats -> writer. Fortschritt: tqdm oder einfache Log-Zeilen (z.B. alle 100 Dateien).

---

## 5. Abhaengigkeiten

- Python 3.10+ (oder 3.9 mit from __future__ annotations).
- numpy (Pflicht).
- tifffile (fuer .tif/.tiff); Pillow (fuer .png, .jpg, .bmp).
- Optional: h5py fuer .h5/.hdf5; pandas optional fuer bequemes CSV (sonst csv + numpy).
- Kein PyQt – reine CLI.

---

## 6. Optionale spaetere DAMPF-Anbindung

- In DAMPF GUI: Button „Skalarstats berechnen“ (z.B. neben „Save DB“).
- Aktion: `python -m scalar_stats --db <db_edit.text()>` (oder Subprocess mit Pfad zum Skript); stdout/stderr im DAMPF-Log anzeigen.
- Keine Statistik-Logik in gui.py – nur Aufruf des externen Programms.

---

## 7. Reihenfolge der Umsetzung (Vorschlag)

1. **config.py + reader.py** – DB und JSONL einlesen, Zeilen mit id/relpath.
2. **loaders.py** – Einzelne Dateitypen (z.B. zuerst .tif, .csv, .npy), dann erweitern.
3. **stats.py** – compute_scalar_stats().
4. **writer.py** – Ausgabe CSV (einfach), dann DB-Erweiterung.
5. **cli.py** – argparse, sequentiell, dann Parallelisierung + Fortschritt.
6. **Tests** – kleine Fixture-Dateien (ein .tif, ein .csv, eine kleine DB); Tests fuer reader, loaders, stats, writer.
7. **Dokumentation** – README mit Beispielaufruf und Option „DAMPF-Button“ erwaehnen.

---
