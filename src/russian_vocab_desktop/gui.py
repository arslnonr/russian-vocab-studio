"""PySide6 desktop GUI for Russian vocab extraction."""

from __future__ import annotations

from pathlib import Path
import sys
import threading
import traceback

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QAction, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .models import ALL_POS_GROUPS, ExtractionOptions, ProgressUpdate
from .pdf_text import get_page_count
from .pipeline import run_extraction


class DropZone(QLabel):
    file_dropped = Signal(Path)
    browse_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(108)
        self.setText(
            "Drop a PDF here or click to browse"
        )
        self.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #4e6f95;
                border-radius: 14px;
                background: #131f30;
                color: #f4f7fb;
                font-size: 15px;
                font-weight: 700;
                padding: 18px;
            }
            """
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        urls = event.mimeData().urls()
        if urls and any(url.toLocalFile().lower().endswith(".pdf") for url in urls):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() == ".pdf":
                self.file_dropped.emit(path)
                event.acceptProposedAction()
                return
        event.ignore()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.browse_requested.emit()
        super().mousePressEvent(event)


class ExtractionWorker(QThread):
    progress = Signal(object)
    log = Signal(str)
    finished_ok = Signal(object)
    failed = Signal(str, str)

    def __init__(self, pdf_path: Path, output_path: Path, options: ExtractionOptions) -> None:
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.options = options
        self.cancel_event = threading.Event()

    def run(self) -> None:
        try:
            summary = run_extraction(
                self.pdf_path,
                self.output_path,
                self.options,
                progress_callback=self._handle_progress,
                log_callback=self.log.emit,
                cancel_event=self.cancel_event,
            )
            self.finished_ok.emit(summary)
        except Exception as exc:
            self.failed.emit(str(exc), traceback.format_exc())

    def _handle_progress(self, update: ProgressUpdate) -> None:
        self.progress.emit(update)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Russian Vocab Studio")
        self.resize(980, 760)
        self.setMinimumSize(900, 700)

        self._pdf_path: Path | None = None
        self._page_count: int | None = None
        self._worker: ExtractionWorker | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        header_row = QHBoxLayout()
        header_row.setSpacing(12)
        root.addLayout(header_row)

        header_left = QVBoxLayout()
        header_left.setSpacing(2)
        header_row.addLayout(header_left, 1)

        title = QLabel("Russian Vocab Studio")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f4f7fb;")
        header_left.addWidget(title)

        subtitle = QLabel("Extract lemmas from a PDF, then export CSV or Word files.")
        subtitle.setStyleSheet("font-size: 13px; color: #9eb1c9;")
        header_left.addWidget(subtitle)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setMinimumWidth(120)
        self.status_label.setStyleSheet(
            "color: #f4f7fb; font-weight: 700; background: #16263a; "
            "border: 1px solid #29415d; border-radius: 10px; padding: 8px 12px;"
        )
        header_row.addWidget(self.status_label, 0, Qt.AlignTop)

        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self._set_pdf)
        self.drop_zone.browse_requested.connect(self._browse_pdf)
        root.addWidget(self.drop_zone)

        files_group = QGroupBox("Files")
        files_layout = QGridLayout(files_group)
        files_layout.setHorizontalSpacing(10)
        files_layout.setVerticalSpacing(10)

        self.pdf_path_edit = QLineEdit()
        self.pdf_path_edit.setReadOnly(True)
        self.pdf_path_edit.setPlaceholderText("Choose a PDF")
        browse_pdf_button = QPushButton("Browse PDF")
        browse_pdf_button.clicked.connect(self._browse_pdf)

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Choose where the output file should be saved")
        browse_output_button = QPushButton("Choose File")
        browse_output_button.clicked.connect(self._browse_output)
        open_output_button = QPushButton("Open Folder")
        open_output_button.clicked.connect(self._open_output_dir)

        files_layout.addWidget(QLabel("Input PDF"), 0, 0)
        files_layout.addWidget(self.pdf_path_edit, 0, 1)
        files_layout.addWidget(browse_pdf_button, 0, 2)
        files_layout.addWidget(QLabel("Output file"), 1, 0)
        files_layout.addWidget(self.output_edit, 1, 1)
        files_layout.addWidget(browse_output_button, 1, 2)
        files_layout.addWidget(open_output_button, 1, 3)

        self.pdf_meta = QLabel("No PDF selected yet.")
        self.pdf_meta.setWordWrap(True)
        self.pdf_meta.setStyleSheet("color: #9eb1c9; font-size: 12px;")
        files_layout.addWidget(self.pdf_meta, 2, 0, 1, 4)
        files_layout.setColumnStretch(1, 1)

        root.addWidget(files_group)

        options_row = QHBoxLayout()
        options_row.setSpacing(12)
        root.addLayout(options_row)

        scope_group = QGroupBox("Scope")
        scope_layout = QGridLayout(scope_group)
        scope_layout.setHorizontalSpacing(10)
        scope_layout.setVerticalSpacing(10)
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(1)
        self.start_spin.setValue(1)
        self.end_spin = QSpinBox()
        self.end_spin.setMinimum(0)
        self.end_spin.setSpecialValueText("Last page")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["auto", "text", "ocr"])
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(100, 600)
        self.dpi_spin.setValue(220)
        scope_layout.addWidget(QLabel("Start page"), 0, 0)
        scope_layout.addWidget(self.start_spin, 0, 1)
        scope_layout.addWidget(QLabel("End page"), 0, 2)
        scope_layout.addWidget(self.end_spin, 0, 3)
        scope_layout.addWidget(QLabel("Reading mode"), 1, 0)
        scope_layout.addWidget(self.mode_combo, 1, 1)
        scope_layout.addWidget(QLabel("OCR DPI"), 1, 2)
        scope_layout.addWidget(self.dpi_spin, 1, 3)
        scope_layout.setColumnStretch(1, 1)
        scope_layout.setColumnStretch(3, 1)
        options_row.addWidget(scope_group, 1)

        export_group = QGroupBox("Export")
        export_layout = QGridLayout(export_group)
        export_layout.setHorizontalSpacing(10)
        export_layout.setVerticalSpacing(10)
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["frequency_desc", "alphabetical"])
        self.export_combo = QComboBox()
        self.export_combo.addItem("Single file", "single_file")
        self.export_combo.addItem("Separate by POS", "separate_by_pos")
        self.export_combo.addItem("Single file + separate by POS", "both")
        self.exclude_edit = QLineEdit()
        self.exclude_edit.setReadOnly(True)
        self.exclude_edit.setPlaceholderText("Optional .txt file with one lemma per line")
        exclude_button = QPushButton("Browse")
        exclude_button.clicked.connect(self._browse_exclude_list)
        clear_exclude_button = QPushButton("Clear")
        clear_exclude_button.clicked.connect(lambda: self.exclude_edit.clear())
        export_layout.addWidget(QLabel("Sort order"), 0, 0)
        export_layout.addWidget(self.sort_combo, 0, 1)
        export_layout.addWidget(QLabel("Export mode"), 0, 2)
        export_layout.addWidget(self.export_combo, 0, 3)
        export_layout.addWidget(QLabel("Custom exclude list"), 1, 0)
        export_layout.addWidget(self.exclude_edit, 1, 1, 1, 2)
        export_layout.addWidget(exclude_button, 1, 3)
        export_layout.addWidget(clear_exclude_button, 1, 4)
        export_layout.setColumnStretch(1, 1)
        export_layout.setColumnStretch(3, 1)
        options_row.addWidget(export_group, 1)

        lower_row = QHBoxLayout()
        lower_row.setSpacing(12)
        root.addLayout(lower_row)

        filter_group = QGroupBox("Filters")
        filter_layout = QGridLayout(filter_group)
        filter_layout.setHorizontalSpacing(10)
        filter_layout.setVerticalSpacing(8)
        self.proper_check = QCheckBox("Remove proper nouns")
        self.proper_check.setChecked(True)
        self.known_check = QCheckBox("Known words only")
        self.known_check.setChecked(True)
        self.basic_check = QCheckBox("Remove basic words")
        self.basic_check.setChecked(True)
        self.freq_check = QCheckBox("Include frequency")
        self.freq_check.setChecked(True)
        self.pos_col_check = QCheckBox("Include POS")
        self.pos_col_check.setChecked(True)
        self.header_check = QCheckBox("Include header")
        self.header_check.setChecked(True)
        self.min_length_spin = QSpinBox()
        self.min_length_spin.setRange(1, 30)
        self.min_length_spin.setValue(2)
        self.min_freq_spin = QSpinBox()
        self.min_freq_spin.setRange(1, 1000)
        self.min_freq_spin.setValue(2)
        filter_layout.addWidget(self.proper_check, 0, 0)
        filter_layout.addWidget(self.known_check, 0, 1)
        filter_layout.addWidget(self.basic_check, 1, 0)
        filter_layout.addWidget(self.freq_check, 1, 1)
        filter_layout.addWidget(self.pos_col_check, 2, 0)
        filter_layout.addWidget(self.header_check, 2, 1)
        filter_layout.addWidget(QLabel("Min token length"), 3, 0)
        filter_layout.addWidget(self.min_length_spin, 3, 1)
        filter_layout.addWidget(QLabel("Min lemma frequency"), 4, 0)
        filter_layout.addWidget(self.min_freq_spin, 4, 1)
        lower_row.addWidget(filter_group, 1)

        pos_group = QGroupBox("Parts of Speech")
        pos_layout = QGridLayout(pos_group)
        pos_layout.setHorizontalSpacing(14)
        pos_layout.setVerticalSpacing(8)
        self.pos_checks: dict[str, QCheckBox] = {}
        pos_labels = {
            "noun": "Nouns",
            "verb": "Verbs",
            "adjective": "Adjectives",
            "adverb": "Adverbs",
            "other": "Other",
        }
        for index, key in enumerate(ALL_POS_GROUPS):
            box = QCheckBox(pos_labels[key])
            box.setChecked(True)
            self.pos_checks[key] = box
            pos_layout.addWidget(box, index // 2, index % 2)
        lower_row.addWidget(pos_group, 1)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        root.addLayout(action_row)

        self.run_button = QPushButton("Extract Vocabulary")
        self.run_button.setMinimumHeight(40)
        self.run_button.clicked.connect(self._toggle_run)
        action_row.addWidget(self.run_button, 1)

        readme_button = QPushButton("Open README")
        readme_button.clicked.connect(self._open_readme)
        action_row.addWidget(readme_button)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.progress_label = QLabel("0 / 0")
        self.progress_label.setStyleSheet("color: #9eb1c9;")
        root.addWidget(self.progress_label)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Progress logs will appear here.")
        self.log_box.setFixedHeight(120)
        self.log_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        root.addWidget(self.log_box)

        about_action = QAction("Open README", self)
        about_action.triggered.connect(self._open_readme)
        self.menuBar().addAction(about_action)

    def _browse_pdf(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose PDF",
            "",
            "PDF Files (*.pdf);;All Files (*)",
        )
        if file_path:
            self._set_pdf(Path(file_path))

    def _browse_output(self) -> None:
        default_path = self.output_edit.text().strip()
        if not default_path and self._pdf_path is not None:
            default_path = str(self._default_output_path(self._pdf_path))

        current_suffix = self._current_output_suffix()
        selected_filter = (
            "Word Documents (*.docx)"
            if current_suffix == ".docx"
            else "CSV Files (*.csv)"
        )

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Choose output file",
            default_path,
            "CSV Files (*.csv);;Word Documents (*.docx)",
            selected_filter,
        )
        if file_path:
            self.output_edit.setText(self._normalize_output_path(file_path, selected_filter))

    def _browse_exclude_list(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose exclude list",
            "",
            "Text Files (*.txt);;All Files (*)",
        )
        if file_path:
            self.exclude_edit.setText(file_path)

    def _set_pdf(self, path: Path) -> None:
        try:
            page_count = get_page_count(path)
        except Exception as exc:
            self._show_error(f"Could not read PDF: {exc}")
            return

        self._pdf_path = path
        self._page_count = page_count
        self.start_spin.setValue(1)
        self.end_spin.setMaximum(page_count)
        self.end_spin.setValue(page_count)
        self.start_spin.setMaximum(page_count)
        self.pdf_path_edit.setText(str(path))
        self.pdf_meta.setText(f"{path}\n{page_count} page(s)")
        auto_output = self._default_output_path(path)
        self.output_edit.setText(str(auto_output))
        self.drop_zone.setText(path.name)
        self._append_log(f"Loaded PDF: {path}")

    def _toggle_run(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel_event.set()
            self.status_label.setText("Stopping...")
            return
        self._start_run()

    def _start_run(self) -> None:
        if self._pdf_path is None:
            self._show_error("Choose a PDF first.")
            return
        if not self.output_edit.text().strip():
            self._browse_output()
            if not self.output_edit.text().strip():
                return

        try:
            options = self._read_options()
        except Exception as exc:
            self._show_error(str(exc))
            return

        output_path = Path(self.output_edit.text().strip())
        self.log_box.clear()
        self.progress.setValue(0)
        self.progress_label.setText("0 / ?")
        self.status_label.setText("Running")
        self.run_button.setText("Stop")

        self._worker = ExtractionWorker(self._pdf_path, output_path, options)
        self._worker.log.connect(self._append_log)
        self._worker.progress.connect(self._update_progress)
        self._worker.finished_ok.connect(self._handle_success)
        self._worker.failed.connect(self._handle_failure)
        self._worker.start()

    def _read_options(self) -> ExtractionOptions:
        selected_pos = frozenset(
            key for key, checkbox in self.pos_checks.items() if checkbox.isChecked()
        )
        if not selected_pos:
            raise ValueError("Select at least one part of speech.")

        exclude_text = self.exclude_edit.text().strip()
        exclude_path = Path(exclude_text) if exclude_text else None
        end_value = self.end_spin.value()
        end_page = None if end_value == 0 else end_value

        return ExtractionOptions(
            start_page=self.start_spin.value(),
            end_page=end_page,
            text_mode=self.mode_combo.currentText(),
            dpi=self.dpi_spin.value(),
            min_length=self.min_length_spin.value(),
            min_frequency=self.min_freq_spin.value(),
            exclude_proper_nouns=self.proper_check.isChecked(),
            known_only=self.known_check.isChecked(),
            exclude_basic_lemmas=self.basic_check.isChecked(),
            custom_exclude_path=exclude_path,
            allowed_pos=selected_pos,
            include_frequency=self.freq_check.isChecked(),
            include_pos=self.pos_col_check.isChecked(),
            include_header=self.header_check.isChecked(),
            sort_mode=self.sort_combo.currentText(),
            export_mode=self.export_combo.currentData(),
        )

    def _update_progress(self, update: ProgressUpdate) -> None:
        total = update.total or 1
        value = int((update.current / total) * 100)
        self.progress.setValue(max(0, min(100, value)))
        self.progress_label.setText(f"{update.current} / {update.total}")
        self.status_label.setText(update.message)

    def _handle_success(self, summary) -> None:
        self.progress.setValue(100)
        self.progress_label.setText("Done")
        self.status_label.setText("Completed")
        self.run_button.setText("Extract Vocabulary")
        self._append_log(
            f"Completed. Kept {summary.kept_lemmas} lemmas. "
            f"Text pages: {summary.text_pages}, OCR pages: {summary.ocr_pages}"
        )
        for path in summary.output_files:
            self._append_log(f"Saved: {path}")
        self._worker = None

    def _handle_failure(self, message: str, details: str) -> None:
        self.status_label.setText("Stopped")
        self.run_button.setText("Extract Vocabulary")
        self._append_log(f"Error: {message}")
        if "Extraction cancelled." not in message:
            self._append_log(details)
        self._worker = None

    def _append_log(self, message: str) -> None:
        self.log_box.appendPlainText(message)

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)

    def _open_output_dir(self) -> None:
        output_text = self.output_edit.text().strip()
        if not output_text:
            return
        QDesktopServices.openUrl(Path(output_text).parent.as_uri())

    def _current_output_suffix(self) -> str:
        output_text = self.output_edit.text().strip()
        if not output_text:
            return ".csv"
        suffix = Path(output_text).suffix.lower()
        if suffix in {".csv", ".docx"}:
            return suffix
        return ".csv"

    def _default_output_path(self, pdf_path: Path) -> Path:
        return pdf_path.with_name(f"{pdf_path.stem}_lemmas{self._current_output_suffix()}")

    def _normalize_output_path(self, file_path: str, selected_filter: str) -> str:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix in {".csv", ".docx"}:
            return str(path)

        default_suffix = ".docx" if "docx" in selected_filter.lower() else ".csv"
        return str(path.with_suffix(default_suffix))

    def _open_readme(self) -> None:
        readme = Path(__file__).resolve().parents[2] / "README.md"
        if readme.exists():
            QDesktopServices.openUrl(readme.as_uri())


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(
        """
        QWidget {
            font-size: 13px;
            color: #edf3fa;
        }
        QMainWindow {
            background: #0d1522;
        }
        QMenuBar {
            background: #111b2b;
            color: #edf3fa;
        }
        QMenuBar::item:selected {
            background: #1b2a40;
        }
        QGroupBox {
            border: 1px solid #29415d;
            border-radius: 14px;
            margin-top: 12px;
            font-weight: 700;
            color: #f4f7fb;
            background: #152132;
            padding-top: 12px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px 0 6px;
            color: #f4f7fb;
        }
        QPushButton {
            background: #d18a2b;
            color: #08111c;
            border: none;
            border-radius: 10px;
            padding: 8px 12px;
            font-weight: 700;
            min-height: 18px;
        }
        QPushButton:hover { background: #e7a243; }
        QPushButton:pressed { background: #bf7720; }
        QLineEdit, QPlainTextEdit, QComboBox, QSpinBox {
            border: 1px solid #35506d;
            border-radius: 10px;
            padding: 6px 8px;
            background: #0f1b2c;
            color: #f4f7fb;
            selection-background-color: #d18a2b;
            selection-color: #08111c;
            min-height: 18px;
        }
        QComboBox QAbstractItemView {
            background: #152132;
            color: #f4f7fb;
            border: 1px solid #35506d;
            selection-background-color: #d18a2b;
            selection-color: #08111c;
        }
        QCheckBox {
            color: #dfe8f2;
            spacing: 6px;
            font-weight: 600;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid #4b6786;
            background: #0f1b2c;
        }
        QCheckBox::indicator:checked {
            background: #d18a2b;
            border: 1px solid #d18a2b;
        }
        QLabel {
            color: #edf3fa;
        }
        QProgressBar {
            border: 1px solid #35506d;
            border-radius: 10px;
            text-align: center;
            background: #0f1b2c;
            color: #edf3fa;
        }
        QProgressBar::chunk {
            background: #d18a2b;
            border-radius: 10px;
        }
        """
    )
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
