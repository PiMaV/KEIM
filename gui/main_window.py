"""
KEIM main window: DB path (browse + full path), image count, stat checkboxes, run.
PySide6; drag-and-drop for .db file.
"""
from __future__ import annotations

import multiprocessing
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QSpinBox,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QGridLayout,
)
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from scalar_stats.worker import run_pipeline
from scalar_stats.reader import get_data_table_count, get_table_names, get_table_columns, get_count_from_table
from scalar_stats.config import load_db_config

# Stat keys for checkboxes (label, key)
STAT_CHOICES = [
    ("Min", "file_min"),
    ("Max", "file_max"),
    ("Mean", "file_mean"),
    ("Std", "file_std"),
    ("Median", "file_median"),
    ("SNR", "file_snr"),
]


def _cpu_default() -> int:
    return max(1, multiprocessing.cpu_count() // 2)


class PipelineThread(QThread):
    """Run pipeline in a thread; signals for progress and log."""
    progress = Signal(int, int, str)
    log_message = Signal(str)
    finished_ok = Signal(int, int)

    def __init__(self, opts: dict, parent=None):
        super().__init__(parent)
        self.opts = opts

    def run(self):
        def on_progress(current: int, total: int, msg: str):
            self.progress.emit(current, total, msg)

        def on_log(msg: str):
            self.log_message.emit(msg)

        self.opts["progress_callback"] = on_progress
        self.opts["log_callback"] = on_log
        try:
            ok, err = run_pipeline(**self.opts)
            self.finished_ok.emit(ok, err)
        except Exception as e:
            self.log_message.emit(f"Error: {e}")
            self.finished_ok.emit(0, 0)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KEIM - Scalar statistics")
        self.setAcceptDrops(True)
        self._thread: PipelineThread | None = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- Database: single path + Browse ---
        grp_db = QGroupBox("Database")
        db_layout = QHBoxLayout()
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setPlaceholderText("Full path to .db or drop file here")
        self.db_path_edit.textChanged.connect(self._on_db_path_changed)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_db)
        db_layout.addWidget(self.db_path_edit)
        db_layout.addWidget(btn_browse)
        grp_db.setLayout(db_layout)
        layout.addWidget(grp_db)

        # --- Image count (read from data table when DB is set) ---
        self.count_label = QLabel("Images: —")
        layout.addWidget(self.count_label)

        # --- Statistics checkboxes ---
        grp_stats = QGroupBox("Statistics")
        grid = QGridLayout()
        self.stat_checks = {}
        for i, (label, key) in enumerate(STAT_CHOICES):
            chk = QCheckBox(label)
            chk.setChecked(True)
            self.stat_checks[key] = chk
            grid.addWidget(chk, i // 3, i % 3)
        grp_stats.setLayout(grid)
        layout.addWidget(grp_stats)

        # --- Output ---
        out_layout = QHBoxLayout()
        out_layout.addWidget(QLabel("Output:"))
        self.out_combo = QComboBox()
        self.out_combo.addItems(["Extend DB", "CSV", "JSON"])
        self.out_path_edit = QLineEdit()
        self.out_path_edit.setPlaceholderText("Path for CSV/JSON")
        btn_out = QPushButton("Save as...")
        btn_out.clicked.connect(self._browse_out_path)
        out_layout.addWidget(self.out_combo)
        out_layout.addWidget(self.out_path_edit)
        out_layout.addWidget(btn_out)
        layout.addLayout(out_layout)

        # --- Workers ---
        worker_layout = QHBoxLayout()
        worker_layout.addWidget(QLabel("Workers:"))
        self.workers_spin = QSpinBox()
        self.workers_spin.setMinimum(1)
        self.workers_spin.setMaximum(64)
        self.workers_spin.setValue(_cpu_default())
        worker_layout.addWidget(self.workers_spin)
        worker_layout.addStretch()
        layout.addLayout(worker_layout)

        # --- Start ---
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self._start_pipeline)
        layout.addWidget(self.start_btn)

        # --- Progress ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # --- Log (small box at bottom for diagnostics) ---
        log_label = QLabel("Log")
        layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setPlaceholderText("Run Start to see: database path, root for images, first file path, errors...")
        layout.addWidget(self.log_text)

    def _on_db_path_changed(self):
        path = self.db_path_edit.text().strip()
        if not path:
            self.count_label.setText("Images: —")
            return
        p = Path(path)
        if not p.is_file():
            self.count_label.setText("Images: —")
            return
        n = get_data_table_count(p)
        self.count_label.setText(f"Images: {n}")
        self._log_db_diagnostic(p, n)

    def _log_db_diagnostic(self, db_path: Path, row_count: int) -> None:
        """Append database load diagnostic to log (used on path change and drop)."""
        cfg = load_db_config(db_path)
        root = cfg.resolve_root(db_path)
        self.log_text.append(f"Loading database: {db_path}")
        self.log_text.append(f"Root for images (from config or DB dir): {root}")
        self.log_text.append(f"Table: {cfg.table_name}, column: {cfg.relative_filepath_column}, rows: {row_count}")
        if row_count == 0:
            tables = get_table_names(db_path)
            self.log_text.append(f"Tables in DB: {', '.join(tables) or '(none)'}")
            if cfg.table_name in tables:
                cols = get_table_columns(db_path, cfg.table_name)
                self.log_text.append(f"Columns in '{cfg.table_name}': {', '.join(cols) or '(none)'}")
            # If default table "data" has rows, config may be wrong
            if "data" in tables and cfg.table_name != "data":
                n_data = get_count_from_table(db_path, "data")
                if n_data > 0:
                    self.log_text.append(f"Note: table 'data' has {n_data} rows; config table_name may be wrong.")
        self.log_text.append("")

    def _browse_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select SQLite database", "", "SQLite (*.db *.sqlite);;All (*)"
        )
        if path:
            self.db_path_edit.setText(path)

    def _browse_out_path(self):
        idx = self.out_combo.currentIndex()
        if idx == 1:
            path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV (*.csv);;All (*)")
        elif idx == 2:
            path, _ = QFileDialog.getSaveFileName(self, "Save JSON", "", "JSON (*.json);;All (*)")
        else:
            return
        if path:
            self.out_path_edit.setText(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return
        path = Path(urls[0].toLocalFile())
        if path.suffix.lower() in (".db", ".sqlite"):
            self.db_path_edit.setText(str(path))
        event.acceptProposedAction()

    def _get_selected_stats(self) -> list[str]:
        return [key for key, chk in self.stat_checks.items() if chk.isChecked()]

    def _start_pipeline(self):
        if self._thread and self._thread.isRunning():
            return
        db_path = self.db_path_edit.text().strip()
        if not db_path:
            QMessageBox.warning(self, "Input", "Please enter the database path.")
            return
        db_path_p = Path(db_path)
        if not db_path_p.is_file():
            QMessageBox.warning(self, "Input", f"File not found: {db_path}")
            return
        stats_keys = self._get_selected_stats()
        if not stats_keys:
            QMessageBox.warning(self, "Statistics", "Select at least one statistic.")
            return
        out_mode = ["db", "csv", "json"][self.out_combo.currentIndex()]
        out_path = self.out_path_edit.text().strip() or None
        if out_mode != "db" and not out_path:
            QMessageBox.warning(self, "Output", "For CSV/JSON please specify output path.")
            return
        opts = {
            "db_path": db_path_p,
            "output_mode": out_mode,
            "workers": self.workers_spin.value(),
            "stats_keys": stats_keys,
        }
        if out_mode != "db" and out_path:
            opts["out_path"] = Path(out_path)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self._thread = PipelineThread(opts, self)
        self._thread.progress.connect(self._on_progress)
        self._thread.log_message.connect(self._on_log)
        self._thread.finished_ok.connect(self._on_finished)
        self._thread.start()

    def _on_progress(self, current: int, total: int, msg: str):
        if total:
            self.progress_bar.setValue(int(100 * current / total))
        self.progress_bar.setFormat(f"{current}/{total}")

    def _on_log(self, msg: str):
        self.log_text.append(msg)

    def _on_finished(self, ok: int, err: int):
        self.start_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Done")
