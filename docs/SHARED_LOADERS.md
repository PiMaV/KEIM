# Zentrales Paket fuer Daten- und Datei-Handling

## Ziel

**Ein zentrales Python-Paket** uebernimmt Daten- und Datei-Handling (Bilder laden, CSV als Matrix, ggf. weitere Formate). Die Programme **Steam, Blitz, KEIM, Wolke** (und evtl. weitere) haengen nur an dieser einen Adresse – sie nutzen das Paket als Abhaengigkeit, ohne die Logik in jedem Projekt zu duplizieren.

Es geht ausdruecklich **nicht** um einen eigenen Dienst oder eine „API“ im Sinne eines Servers, sondern um **ein gemeinsames Modul/Paket**, das alle vier aufrufen. Die „API“ ist schlicht die Art, wie man das Paket nutzt (welche Funktionen es exportiert, z. B. `load_image_2d`, `load_csv_2d`).

---

## Aktuelle Verteilung (vor der Zentralisierung)

| Programm | Bild laden | CSV/Matrix | Ablage |
|----------|------------|------------|--------|
| **KEIM** | tifffile + PIL, max 3D (H,W,C), 2D-Intensitaet | CSV/TSV als 2D-Matrix (Zeilen x Spalten) | `scalar_stats/loaders.py` |
| **BLITZ** | cv2 (BGR/RGB), Video, .npy | tof_from_csv (2 Spalten), tof_from_json | `blitz/data/load.py` |
| **WOLKE** | PIL + .npy (2D/3D), normalize_image | – | `wolke/utils.py` (load_image_as_array) |

Gemeinsam gebraucht werden faktisch:

- **Bilder**: Pfad → 2D/3D numpy (max 3D, 3. Dim = Kanaele; Reduktion auf 2D Intensitaet).
- **CSV**: Pfad → 2D-Matrix (Zeilen x Spalten) oder spezielle Formate (z. B. 2 Spalten).
- **Konstanten**: z. B. `IMAGE_EXT`, `CSV_EXT` / `IMAGE_EXTENSIONS`, `ARRAY_EXTENSIONS`.

---

## Vorteile eines zentralen Pakets

- Einheitliches Verhalten in allen Programmen (z. B. 3D→2D, CSV als Matrix).
- Keine Duplikate: Aenderungen (neue Formate, Fehlerbehandlung) nur an einer Stelle.
- Steam, Blitz, KEIM, Wolke importieren dasselbe Paket; kein Code-Chaos durch parallele Kopien.

---

## Was das zentrale Paket abdecken soll

- **Kern-Funktionen** (gleiche Signatur in allen Projekten):
  - `load_image_2d(path)` → 2D-Array oder Fehler (bei 3D: Kanaele auf Intensitaet reduzieren).
  - `load_file_as_array(path)` → 1D-Array (z. B. fuer Skalarstatistiken; aus Bild oder CSV-Matrix).
  - `load_csv_2d(path)` → 2D-Matrix (Zeilen x Spalten).
  - Konstanten: `IMAGE_EXT`, `CSV_EXT` (evtl. `VIDEO_EXT`, `ARRAY_EXT` fuer BLITZ).

- **Projekt-spezifisch bleiben** (bleiben in Steam/Blitz/KEIM/Wolke):
  - BLITZ: Video-Laden, RAM/Subset, Preview, Metadata.
  - WOLKE: normalize_image, Dash/State.
  - KEIM: Pipeline (DB/index.jsonl), Statistik-Berechnung.

---

## Umsetzung: Wie setzen wir das am besten um?

Zwei sinnvolle Varianten:

### Option A: Eigenes kleines Repo

- Neues **eigenes Repo** (z. B. `shared-data-io` oder `picture-data-loader`).
- Enthaelt nur das zentrale Paket (pyproject.toml, `src/<paketname>/` mit Loader-Logik).
- Steam, Blitz, KEIM, Wolke fuegen das Repo als Abhaengigkeit hinzu (z. B. `uv add git+https://...` oder lokaler Pfad `uv add ../shared-data-io`).
- **Vorteil**: Klar getrennt, versionierbar, unabhaengig von einem einzelnen Projekt. Gut, wenn mehrere Leute oder Repos dran arbeiten.

### Option B: Eigener Ordner im Root (Monorepo)

- Im **Ueberordner** (z. B. `c:\Cursor\`) ein eigener Ordner, z. B. `shared_data_io/` oder `common/`.
- Darin: pyproject.toml + Quellcode des Pakets (z. B. `src/shared_data_io/`).
- Die vier Projekte liegen daneben (KEIM, BLITZ, WOLKE, …) und referenzieren das Paket per Pfad, z. B. `uv add ../shared_data_io`.
- **Vorteil**: Alles an einem Ort, einfache lokale Aenderungen; kein zweites Repo noetig.

### Inhalt: „Bestes aus allen Welten“ zusammenfuehren

Unabhaengig von A oder B:

1. **Gemeinsame Schnittstelle festlegen**  
   Die oben genannten Funktionen (`load_image_2d`, `load_csv_2d`, `load_file_as_array`) und Konstanten als **einzige** Einstiegspunkte.

2. **Bestehende Loader sichten und zusammenfuehren**  
   - Aus **KEIM** `loaders.py`: CSV als 2D-Matrix, Bild 2D/3D mit Reduktion, tifffile/PIL (oder Backend-Wahl).
   - Aus **BLITZ** `load.py`: cv2-Bildladen, IMAGE_EXTENSIONS/ARRAY_EXTENSIONS, evtl. .npy-Handling.
   - Aus **WOLKE** `utils.py`: load_image_as_array-Logik, evtl. .npy.

3. **Ein Implementierungs-Mix bauen**  
   - Ein Backend waehlen (z. B. cv2 fuer Bilder, weil BLITZ es eh nutzt und gut unterstuetzt) oder optional zwei Backends (cv2 / PIL+tifffile) mit einer einheitlichen Funktion.
   - CSV: die 2D-Matrix-Logik aus KEIM uebernehmen (Zeilen x Spalten, rechteckig).
   - .npy/.npz: wie in KEIM oder BLITZ – einmal festlegen und im zentralen Paket umsetzen.

4. **Projekte nacheinander umstellen**  
   Zuerst eines (z. B. KEIM), dann die anderen: Im jeweiligen Projekt den lokalen Loader durch `from shared_data_io import load_image_2d, load_csv_2d, load_file_as_array` ersetzen und pruefen, dass Tests/Verhalten gleich bleiben.

**Kurz:** Eigenes kleines Repo **oder** eigener Ordner im Root – dann die **jeweiligen Loader aus KEIM, BLITZ, WOLKE sichten und das Beste daraus im zentralen Paket zusammenfuehren**. Die Projekte werden reine „Abnehmer“ des einen Pakets.
