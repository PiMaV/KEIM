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

- PyInstaller installieren: `pip install pyinstaller`
- Im Projektverzeichnis (KEIM):  
  `pyinstaller build.spec`
- **Windows:** Fertige Datei: `dist/keim.exe` (one-file).
- **Ubuntu/Linux:** Auf einer Linux-Umgebung (z.B. Ubuntu oder WSL) denselben Befehl ausfuehren → `dist/keim` (ausfuehrbares Binary).

Hinweis: Windows-.exe muss unter Windows gebaut werden, das Linux-Binary unter Linux – plattformuebergreifendes Bauen wird von PyInstaller nicht unterstuetzt.

## Optionale DAMPF-Anbindung

In DAMPF kann ein Button „Skalarstats berechnen“ die fertige KEIM-.exe aufrufen, z.B.:

`keim.exe --db <DB-Pfad aus dem DAMPF-Dialog>`

Die Ausgabe erscheint in der Konsole bzw. kann von DAMPF aus gelesen werden (z.B. Subprocess mit stdout/stderr ins Log).

## Tests

Aus dem Projektverzeichnis: `python -m pytest tests/`

## Projektstruktur

- `main.py` – Einstieg (GUI oder Headless)
- `scalar_stats/` – reader, loaders, stats, writer, config, worker
- `gui/` – Hauptfenster (PySide6)
- `build.spec` – PyInstaller-Spec fuer keim.exe / keim (Linux)
