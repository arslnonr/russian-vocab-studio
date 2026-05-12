"""
Russian Vocab Studio – PySide6 desktop app

Açık tema, kart tabanlı düzen, TR/RU/EN dil desteği.
Uzun işlemler QThread'da çalışır, ana thread bloklanmaz.

Run:
    python app.py
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    Qt, QThread, Signal,
)
from PySide6.QtGui import (
    QDragEnterEvent, QDropEvent, QFont, QFontDatabase,
)
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
)

import threading

from extractor import (
    Cancelled, ExtractError, ExtractOptions, ExtractResult, extract,
)
from translations import I18n, LANGUAGES


# --------------------------------------------------------------------------- #
# Design tokens
# --------------------------------------------------------------------------- #

BG          = "#FAFAF7"
SURFACE     = "#FFFFFF"
SURFACE_ALT = "#F4F3EE"
BORDER      = "#E6E4DD"
TEXT        = "#15171A"
MUTED       = "#7A7A75"
ACCENT      = "#3B62FF"
ACCENT_HOV  = "#2547D9"
ACCENT_SOFT = "#E9EEFF"
SUCCESS     = "#2C8C5A"
DANGER      = "#C94B4B"


# Global stylesheet — applied once on the QApplication.
STYLESHEET = f"""
QWidget {{
    color: {TEXT};
    font-size: 13px;
}}
QMainWindow, QScrollArea, #scrollContent {{
    background: {BG};
    border: none;
}}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: #D8D5CC;
    border-radius: 5px;
    min-height: 32px;
}}
QScrollBar::handle:vertical:hover {{ background: #BFBCB1; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

#title {{ font-size: 22px; font-weight: 600; color: {TEXT}; }}
#subtitle {{ font-size: 13px; color: {MUTED}; }}
#muted {{ color: {MUTED}; }}
#cardTitle {{ font-size: 13px; font-weight: 600; color: {TEXT}; }}

#statusChip {{
    background: {SURFACE};
    color: {MUTED};
    border: 1px solid {BORDER};
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 11px;
}}
#statusChip[state="working"] {{ color: {ACCENT}; }}
#statusChip[state="done"] {{ color: {SUCCESS}; }}
#statusChip[state="error"] {{ color: {DANGER}; }}

QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}

QFrame#dropZone {{
    background: {SURFACE_ALT};
    border: 1px dashed {BORDER};
    border-radius: 12px;
}}
QFrame#dropZone[active="true"] {{
    background: {ACCENT_SOFT};
    border: 1px dashed {ACCENT};
}}

QLineEdit, QSpinBox, QComboBox {{
    background: {SURFACE_ALT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 22px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {ACCENT};
    background: {SURFACE};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 16px;
    border: none;
}}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT};
    outline: 0;
    padding: 4px;
}}

QPushButton {{
    background: {SURFACE_ALT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 14px;
    min-height: 22px;
}}
QPushButton:hover {{ background: {BORDER}; }}
QPushButton:pressed {{ background: {SURFACE}; }}
QPushButton:disabled {{ color: {MUTED}; }}

QPushButton#primary {{
    background: {ACCENT};
    color: white;
    border: 1px solid {ACCENT};
    font-weight: 600;
    padding: 12px 18px;
    font-size: 14px;
    border-radius: 12px;
}}
QPushButton#primary:hover {{ background: {ACCENT_HOV}; border-color: {ACCENT_HOV}; }}
QPushButton#primary:disabled {{ background: #B6BFE8; border-color: #B6BFE8; color: #fff; }}

QPushButton#danger {{
    background: {SURFACE};
    color: {DANGER};
    border: 1px solid {BORDER};
    font-weight: 600;
    padding: 12px 18px;
    font-size: 14px;
    border-radius: 12px;
}}
QPushButton#danger:hover {{ background: #F8EDED; }}

QPushButton#pill {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    color: {TEXT};
    border-radius: 999px;
    padding: 6px 14px;
}}
QPushButton#pill:hover {{ background: {SURFACE_ALT}; }}
QPushButton#pill[on="true"] {{
    background: {ACCENT};
    color: white;
    border: 1px solid {ACCENT};
}}
QPushButton#pill[on="true"]:hover {{ background: {ACCENT_HOV}; border-color: {ACCENT_HOV}; }}

QPushButton#linklike {{
    background: transparent;
    border: none;
    color: {MUTED};
    text-align: left;
    padding: 4px 0;
}}
QPushButton#linklike:hover {{ color: {TEXT}; }}

QCheckBox {{ color: {TEXT}; spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
    image: none;
}}
QCheckBox::indicator:hover {{ border: 1px solid {ACCENT}; }}

QProgressBar {{
    background: {SURFACE_ALT};
    border: none;
    border-radius: 3px;
    height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 3px;
}}

#log[state="info"] {{ color: {MUTED}; }}
#log[state="success"] {{ color: {SUCCESS}; }}
#log[state="error"] {{ color: {DANGER}; }}
"""


# --------------------------------------------------------------------------- #
# Reusable widgets
# --------------------------------------------------------------------------- #


class Card(QFrame):
    """Bordered, rounded white card with an optional title."""

    def __init__(self, title: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 14, 18, 16)
        self._layout.setSpacing(10)

        self.title_label: Optional[QLabel] = None
        if title:
            self.title_label = QLabel(title)
            self.title_label.setObjectName("cardTitle")
            self._layout.addWidget(self.title_label)

    def add(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)

    def add_layout(self, layout) -> None:
        self._layout.addLayout(layout)

    def set_title(self, text: str) -> None:
        if self.title_label is not None:
            self.title_label.setText(text)


class Pill(QPushButton):
    """Toggleable pill — emits toggled() when state flips."""

    def __init__(self, text: str = "", on: bool = True, parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self.setObjectName("pill")
        self.setCheckable(True)
        self.setChecked(on)
        self.setProperty("on", "true" if on else "false")
        self.setCursor(Qt.PointingHandCursor)
        self.toggled.connect(self._on_toggled)
        self._refresh()

    def _on_toggled(self, checked: bool) -> None:
        self.setProperty("on", "true" if checked else "false")
        self._refresh()

    def _refresh(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)


class DropZone(QFrame):
    """A click + drag-drop target for picking a PDF."""

    file_dropped = Signal(Path)
    clicked = Signal()

    def __init__(self, hint_text: str = ""):
        super().__init__()
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(132)
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 22, 20, 22)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        self.icon = QLabel("📄")
        font = self.icon.font()
        font.setPointSize(28)
        self.icon.setFont(font)
        self.icon.setAlignment(Qt.AlignCenter)
        self.icon.setStyleSheet(f"color: {MUTED};")
        layout.addWidget(self.icon)

        self.hint = QLabel(hint_text)
        self.hint.setObjectName("muted")
        self.hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.hint)

    def set_hint(self, text: str) -> None:
        self.hint.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        urls = event.mimeData().urls()
        if urls and any(u.toLocalFile().lower().endswith(".pdf") for u in urls):
            event.acceptProposedAction()
            self.setProperty("active", "true")
            self._restyle()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("active", "false")
        self._restyle()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("active", "false")
        self._restyle()
        for url in event.mimeData().urls():
            p = Path(url.toLocalFile())
            if p.suffix.lower() == ".pdf":
                self.file_dropped.emit(p)
                event.acceptProposedAction()
                return
        event.ignore()

    def _restyle(self) -> None:
        self.style().unpolish(self)
        self.style().polish(self)


# --------------------------------------------------------------------------- #
# Worker thread
# --------------------------------------------------------------------------- #


class ExtractWorker(QThread):
    progress = Signal(float)
    stage = Signal(str)              # 'ocr_init', 'ocr_running', etc.
    finished_ok = Signal(object)     # ExtractResult
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, opts: ExtractOptions):
        super().__init__()
        self.opts = opts
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            def cb(p: float, msg: str) -> None:
                if p < 0:
                    # Negative progress is used as a side-channel for stage names.
                    self.stage.emit(msg)
                else:
                    self.progress.emit(p)
            result = extract(self.opts, on_progress=cb, cancel=self.cancel_event)
            self.finished_ok.emit(result)
        except Cancelled:
            self.cancelled.emit()
        except ExtractError as e:
            self.failed.emit(f"__KEY__:{e.key}:{repr(e.fmt)}")
        except Exception as e:
            tb = traceback.format_exc(limit=2)
            self.failed.emit(f"{e}\n{tb}")


# --------------------------------------------------------------------------- #
# Main window
# --------------------------------------------------------------------------- #


class MainWindow(QMainWindow):
    POS_KEYS = ("noun", "verb", "adj", "adv", "other")
    READING_KEYS = ("auto", "text", "ocr")
    SORT_KEYS = ("frequency", "alpha")
    EXPORT_KEYS = ("single_csv", "separate_by_pos", "both")

    def __init__(self):
        super().__init__()
        self.i18n = I18n("tr")

        self.setWindowTitle("Russian Vocab Studio")
        self.resize(780, 880)
        self.setMinimumSize(720, 760)

        self._pdf_path: Optional[Path] = None
        self._csv_path: Optional[Path] = None
        self._exclude_path: Optional[Path] = None
        self._page_count = 0
        self._worker: Optional[ExtractWorker] = None
        self._adv_open = False

        self._build()
        self._retranslate()

    # ---------------------------- layout ---------------------------- #

    def _build(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        content = QWidget()
        content.setObjectName("scrollContent")
        scroll.setWidget(content)

        outer = QVBoxLayout(content)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        self._build_header(outer)
        self._build_pdf(outer)
        self._build_pages(outer)
        self._build_pos(outer)
        self._build_filters(outer)            # min length / min frequency — top-level
        self._build_advanced_toggle(outer)
        self._build_advanced_section(outer)
        self._build_output(outer)
        self._build_action(outer)
        self._build_status(outer)

        outer.addStretch(1)

    def _build_header(self, parent: QVBoxLayout) -> None:
        bar = QHBoxLayout()
        bar.setSpacing(12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("title")
        text_col.addWidget(self.title_lbl)
        self.subtitle_lbl = QLabel()
        self.subtitle_lbl.setObjectName("subtitle")
        text_col.addWidget(self.subtitle_lbl)
        bar.addLayout(text_col, 1)

        self.status_chip = QLabel()
        self.status_chip.setObjectName("statusChip")
        self.status_chip.setProperty("state", "ready")
        bar.addWidget(self.status_chip, 0, Qt.AlignTop)

        self.lang_combo = QComboBox()
        for code, name in LANGUAGES:
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(0)
        self.lang_combo.setMinimumWidth(120)
        self.lang_combo.currentIndexChanged.connect(self._on_language_change)
        bar.addWidget(self.lang_combo, 0, Qt.AlignTop)

        parent.addLayout(bar)

    def _build_pdf(self, parent: QVBoxLayout) -> None:
        self.pdf_card = Card()
        self.pdf_card_title = QLabel()
        self.pdf_card_title.setObjectName("cardTitle")
        self.pdf_card.add(self.pdf_card_title)

        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.clicked.connect(self._pick_pdf)
        self.drop_zone.file_dropped.connect(self._set_pdf)
        self.pdf_card.add(self.drop_zone)

        # Selected file row (hidden until a PDF is picked)
        self.pdf_info = QFrame()
        info_layout = QHBoxLayout(self.pdf_info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)

        self.pdf_name_lbl = QLabel()
        info_layout.addWidget(self.pdf_name_lbl, 1)

        self.pdf_meta_lbl = QLabel()
        self.pdf_meta_lbl.setObjectName("muted")
        info_layout.addWidget(self.pdf_meta_lbl, 0)

        self.pdf_change_btn = QPushButton()
        self.pdf_change_btn.clicked.connect(self._pick_pdf)
        info_layout.addWidget(self.pdf_change_btn, 0)

        self.pdf_info.setVisible(False)
        self.pdf_card.add(self.pdf_info)

        parent.addWidget(self.pdf_card)

    def _build_pages(self, parent: QVBoxLayout) -> None:
        self.pages_card = Card()
        self.pages_card_title = QLabel()
        self.pages_card_title.setObjectName("cardTitle")
        self.pages_card.add(self.pages_card_title)

        row = QHBoxLayout()
        row.setSpacing(10)

        self.lbl_start = QLabel()
        self.lbl_start.setObjectName("muted")
        row.addWidget(self.lbl_start)

        self.start_spin = QSpinBox()
        self.start_spin.setRange(1, 99999)
        self.start_spin.setValue(1)
        self.start_spin.setMinimumWidth(80)
        row.addWidget(self.start_spin)

        self.lbl_end = QLabel()
        self.lbl_end.setObjectName("muted")
        row.addWidget(self.lbl_end)

        self.end_spin = QSpinBox()
        self.end_spin.setRange(1, 99999)
        self.end_spin.setValue(1)
        self.end_spin.setMinimumWidth(80)
        row.addWidget(self.end_spin)

        self.all_pages_chk = QCheckBox()
        self.all_pages_chk.setChecked(True)
        self.all_pages_chk.toggled.connect(self._on_all_pages_toggle)
        row.addWidget(self.all_pages_chk)

        row.addStretch(1)
        self.pages_card.add_layout(row)

        self._on_all_pages_toggle(True)
        parent.addWidget(self.pages_card)

    def _build_pos(self, parent: QVBoxLayout) -> None:
        self.pos_card = Card()
        self.pos_card_title = QLabel()
        self.pos_card_title.setObjectName("cardTitle")
        self.pos_card.add(self.pos_card_title)

        row = QHBoxLayout()
        row.setSpacing(8)
        self.pos_pills: dict[str, Pill] = {}
        for key in self.POS_KEYS:
            on = key != "other"
            pill = Pill(on=on)
            self.pos_pills[key] = pill
            row.addWidget(pill)
        row.addStretch(1)
        self.pos_card.add_layout(row)

        parent.addWidget(self.pos_card)

    def _build_advanced_toggle(self, parent: QVBoxLayout) -> None:
        self.adv_btn = QPushButton()
        self.adv_btn.setObjectName("linklike")
        self.adv_btn.setCursor(Qt.PointingHandCursor)
        self.adv_btn.clicked.connect(self._toggle_advanced)
        parent.addWidget(self.adv_btn)

    def _build_filters(self, parent: QVBoxLayout) -> None:
        """Top-level filters card — min length, min frequency, basic stoplist."""
        self.filters_card = Card()
        self.filters_card_title = QLabel()
        self.filters_card_title.setObjectName("cardTitle")
        self.filters_card.add(self.filters_card_title)

        # Number filters in a single row, big and visible.
        nrow = QHBoxLayout()
        nrow.setSpacing(20)

        # Min length
        len_col = QHBoxLayout()
        len_col.setSpacing(8)
        self.lbl_min_len = QLabel()
        self.lbl_min_len.setObjectName("muted")
        len_col.addWidget(self.lbl_min_len)
        self.min_len_spin = QSpinBox()
        self.min_len_spin.setRange(1, 30)
        self.min_len_spin.setValue(3)
        self.min_len_spin.setMinimumWidth(80)
        len_col.addWidget(self.min_len_spin)
        nrow.addLayout(len_col)

        # Min frequency
        freq_col = QHBoxLayout()
        freq_col.setSpacing(8)
        self.lbl_min_freq = QLabel()
        self.lbl_min_freq.setObjectName("muted")
        freq_col.addWidget(self.lbl_min_freq)
        self.min_freq_spin = QSpinBox()
        self.min_freq_spin.setRange(1, 9999)
        self.min_freq_spin.setValue(2)
        self.min_freq_spin.setMinimumWidth(80)
        freq_col.addWidget(self.min_freq_spin)
        nrow.addLayout(freq_col)

        nrow.addStretch(1)
        self.filters_card.add_layout(nrow)

        # Hint line explaining the defaults
        self.filters_hint_lbl = QLabel()
        self.filters_hint_lbl.setObjectName("muted")
        self.filters_hint_lbl.setWordWrap(True)
        self.filters_card.add(self.filters_hint_lbl)

        # Toggles row
        trow = QHBoxLayout()
        trow.setSpacing(20)

        self.chk_proper = QCheckBox()
        self.chk_proper.setChecked(True)
        trow.addWidget(self.chk_proper)

        self.chk_basic = QCheckBox()
        self.chk_basic.setChecked(True)
        trow.addWidget(self.chk_basic)

        trow.addStretch(1)
        self.filters_card.add_layout(trow)

        parent.addWidget(self.filters_card)

    def _build_advanced_section(self, parent: QVBoxLayout) -> None:
        self.adv_widget = QWidget()
        adv_layout = QVBoxLayout(self.adv_widget)
        adv_layout.setContentsMargins(0, 0, 0, 0)
        adv_layout.setSpacing(14)

        # Reading mode
        self.reading_card = Card()
        self.reading_card_title = QLabel()
        self.reading_card_title.setObjectName("cardTitle")
        self.reading_card.add(self.reading_card_title)

        r_row = QHBoxLayout()
        self.reading_combo = QComboBox()
        self.reading_combo.setMinimumWidth(220)
        # Items added during retranslate.
        r_row.addWidget(self.reading_combo, 0)
        r_row.addStretch(1)
        self.reading_card.add_layout(r_row)
        adv_layout.addWidget(self.reading_card)

        # Sort + flags
        self.sort_card = Card()
        self.sort_card_title = QLabel()
        self.sort_card_title.setObjectName("cardTitle")
        self.sort_card.add(self.sort_card_title)

        s_row = QHBoxLayout()
        s_row.setSpacing(12)
        self.lbl_sort = QLabel()
        self.lbl_sort.setObjectName("muted")
        s_row.addWidget(self.lbl_sort)
        self.sort_combo = QComboBox()
        self.sort_combo.setMinimumWidth(220)
        s_row.addWidget(self.sort_combo)

        self.chk_inc_freq = QCheckBox()
        self.chk_inc_freq.setChecked(True)
        s_row.addWidget(self.chk_inc_freq)

        self.chk_inc_pos = QCheckBox()
        self.chk_inc_pos.setChecked(True)
        s_row.addWidget(self.chk_inc_pos)

        s_row.addStretch(1)
        self.sort_card.add_layout(s_row)
        adv_layout.addWidget(self.sort_card)

        # Custom exclude list (its own card now — export mode moved to Output card)
        self.exclude_card = Card()
        self.exclude_card_title = QLabel()
        self.exclude_card_title.setObjectName("cardTitle")
        self.exclude_card.add(self.exclude_card_title)

        ex_row = QHBoxLayout()
        ex_row.setSpacing(8)
        self.exclude_label = QLabel()
        self.exclude_label.setObjectName("muted")
        ex_row.addWidget(self.exclude_label, 1)
        self.exclude_pick_btn = QPushButton()
        self.exclude_pick_btn.clicked.connect(self._pick_exclude)
        ex_row.addWidget(self.exclude_pick_btn)
        self.exclude_clear_btn = QPushButton()
        self.exclude_clear_btn.clicked.connect(self._clear_exclude)
        ex_row.addWidget(self.exclude_clear_btn)
        self.exclude_card.add_layout(ex_row)

        adv_layout.addWidget(self.exclude_card)

        self.adv_widget.setVisible(False)
        parent.addWidget(self.adv_widget)

    def _build_output(self, parent: QVBoxLayout) -> None:
        self.output_card = Card()
        self.output_card_title = QLabel()
        self.output_card_title.setObjectName("cardTitle")
        self.output_card.add(self.output_card_title)

        # Export mode row — single CSV vs split-by-POS
        mode_row = QHBoxLayout()
        mode_row.setSpacing(12)
        self.lbl_export = QLabel()
        self.lbl_export.setObjectName("muted")
        mode_row.addWidget(self.lbl_export)
        self.export_combo = QComboBox()
        self.export_combo.setMinimumWidth(220)
        mode_row.addWidget(self.export_combo)
        mode_row.addStretch(1)
        self.output_card.add_layout(mode_row)

        # Hint reminding the user how to limit POS
        self.export_hint_lbl = QLabel()
        self.export_hint_lbl.setObjectName("muted")
        self.export_hint_lbl.setWordWrap(True)
        self.output_card.add(self.export_hint_lbl)

        # File path row
        row = QHBoxLayout()
        row.setSpacing(8)

        self.csv_edit = QLineEdit()
        self.csv_edit.setPlaceholderText("…/words.csv")
        row.addWidget(self.csv_edit, 1)

        self.csv_btn = QPushButton("…")
        self.csv_btn.setMinimumWidth(48)
        self.csv_btn.clicked.connect(self._pick_csv)
        row.addWidget(self.csv_btn)

        self.open_folder_btn = QPushButton()
        self.open_folder_btn.clicked.connect(self._open_output_folder)
        row.addWidget(self.open_folder_btn)

        self.output_card.add_layout(row)
        parent.addWidget(self.output_card)

    def _build_action(self, parent: QVBoxLayout) -> None:
        row = QHBoxLayout()
        row.setSpacing(8)

        self.action_btn = QPushButton()
        self.action_btn.setObjectName("primary")
        self.action_btn.setMinimumHeight(52)
        self.action_btn.clicked.connect(self._on_extract_clicked)
        row.addWidget(self.action_btn, 1)

        self.cancel_btn = QPushButton()
        self.cancel_btn.setObjectName("danger")
        self.cancel_btn.setMinimumHeight(52)
        self.cancel_btn.setMinimumWidth(140)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setVisible(False)
        row.addWidget(self.cancel_btn, 0)

        parent.addLayout(row)

    def _build_status(self, parent: QVBoxLayout) -> None:
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        parent.addWidget(self.progress)

        self.log_lbl = QLabel("")
        self.log_lbl.setObjectName("log")
        self.log_lbl.setProperty("state", "info")
        self.log_lbl.setWordWrap(True)
        parent.addWidget(self.log_lbl)

    # ---------------------------- i18n ---------------------------- #

    def _on_language_change(self, idx: int) -> None:
        code = self.lang_combo.itemData(idx) or "tr"
        self.i18n.set(code)
        self._retranslate()

    def _retranslate(self) -> None:
        t = self.i18n.t

        self.setWindowTitle(t("app_title"))
        self.title_lbl.setText(t("app_title"))
        self.subtitle_lbl.setText(t("app_subtitle"))
        self._set_status(t("status_ready"), state="ready")

        self.pdf_card_title.setText(t("pdf_card_title"))
        self.drop_zone.set_hint(t("pdf_drop_hint"))
        self.pdf_change_btn.setText(t("pdf_change"))
        self._refresh_pdf_meta()

        self.pages_card_title.setText(t("pages_card_title"))
        self.lbl_start.setText(t("pages_start"))
        self.lbl_end.setText(t("pages_end"))
        self.all_pages_chk.setText(t("pages_all"))

        self.pos_card_title.setText(t("pos_card_title"))
        for key, pill in self.pos_pills.items():
            pill.setText(t(f"pos_{key}"))

        self.adv_btn.setText(
            ("▴ " if self._adv_open else "▾ ")
            + (t("advanced_hide") if self._adv_open else t("advanced_show"))
        )

        self.filters_card_title.setText(t("filters_card_title"))
        self.chk_proper.setText(t("filter_remove_proper"))
        self.chk_basic.setText(t("filter_remove_basic"))
        self.lbl_min_len.setText(t("filter_min_length"))
        self.lbl_min_freq.setText(t("filter_min_freq"))
        self.filters_hint_lbl.setText(t("filters_hint"))

        # Reading combo
        self.reading_card_title.setText(t("reading_card_title"))
        prev_reading = self.reading_combo.currentData() or "auto"
        self.reading_combo.blockSignals(True)
        self.reading_combo.clear()
        for k in self.READING_KEYS:
            self.reading_combo.addItem(t(f"reading_{k}"), k)
        idx = self.READING_KEYS.index(prev_reading) if prev_reading in self.READING_KEYS else 0
        self.reading_combo.setCurrentIndex(idx)
        self.reading_combo.blockSignals(False)

        # Sort combo
        self.sort_card_title.setText(t("output_sort"))
        self.lbl_sort.setText(t("output_sort"))
        prev_sort = self.sort_combo.currentData() or "frequency"
        self.sort_combo.blockSignals(True)
        self.sort_combo.clear()
        self.sort_combo.addItem(t("sort_freq"), "frequency")
        self.sort_combo.addItem(t("sort_alpha"), "alpha")
        idx = 0 if prev_sort == "frequency" else 1
        self.sort_combo.setCurrentIndex(idx)
        self.sort_combo.blockSignals(False)
        self.chk_inc_freq.setText(t("output_include_freq"))
        self.chk_inc_pos.setText(t("output_include_pos"))

        # Export combo (now lives in the Output card)
        self.lbl_export.setText(t("export_mode"))
        prev_export = self.export_combo.currentData() or "single_csv"
        self.export_combo.blockSignals(True)
        self.export_combo.clear()
        for k, lab in zip(self.EXPORT_KEYS, ("export_single", "export_separate", "export_both")):
            self.export_combo.addItem(t(lab), k)
        idx = self.EXPORT_KEYS.index(prev_export) if prev_export in self.EXPORT_KEYS else 0
        self.export_combo.setCurrentIndex(idx)
        self.export_combo.blockSignals(False)
        self.export_hint_lbl.setText(t("export_hint"))

        # Custom exclude
        self.exclude_card_title.setText(t("exclude_card_title"))
        if self._exclude_path is None:
            self.exclude_label.setText(t("exclude_none"))
        else:
            self.exclude_label.setText(f"📄  {self._exclude_path.name}")
        self.exclude_pick_btn.setText(t("exclude_pick"))
        self.exclude_clear_btn.setText(t("exclude_clear"))

        self.output_card_title.setText(t("output_card_title"))
        self.open_folder_btn.setText(t("output_open_folder"))

        self.action_btn.setText(t("action_extract"))
        self.cancel_btn.setText(t("action_cancel"))

    # ---------------------------- behavior ---------------------------- #

    def _set_status(self, text: str, state: str = "ready") -> None:
        self.status_chip.setText(text)
        self.status_chip.setProperty("state", state)
        self.status_chip.style().unpolish(self.status_chip)
        self.status_chip.style().polish(self.status_chip)

    def _set_log(self, text: str, state: str = "info") -> None:
        self.log_lbl.setText(text)
        self.log_lbl.setProperty("state", state)
        self.log_lbl.style().unpolish(self.log_lbl)
        self.log_lbl.style().polish(self.log_lbl)

    def _on_all_pages_toggle(self, checked: bool) -> None:
        self.start_spin.setEnabled(not checked)
        self.end_spin.setEnabled(not checked)

    def _toggle_advanced(self) -> None:
        self._adv_open = not self._adv_open
        self.adv_widget.setVisible(self._adv_open)
        self.adv_btn.setText(
            ("▴ " if self._adv_open else "▾ ")
            + (self.i18n.t("advanced_hide") if self._adv_open
               else self.i18n.t("advanced_show"))
        )

    # ---------------------------- file picking ---------------------------- #

    def _pick_pdf(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, self.i18n.t("dlg_pdf_title"), "",
            self.i18n.t("dlg_pdf_filter"),
        )
        if path:
            self._set_pdf(Path(path))

    def _set_pdf(self, path: Path) -> None:
        self._pdf_path = path
        self._page_count = 0
        try:
            import fitz  # type: ignore
            with fitz.open(path) as doc:
                self._page_count = doc.page_count
        except Exception:
            self._page_count = 0

        if not self.csv_edit.text().strip():
            self.csv_edit.setText(str(path.with_suffix(".csv")))

        if self._page_count:
            self.start_spin.setRange(1, self._page_count)
            self.end_spin.setRange(1, self._page_count)
            self.end_spin.setValue(self._page_count)

        self._refresh_pdf_meta()

    def _refresh_pdf_meta(self) -> None:
        if self._pdf_path is None:
            self.drop_zone.setVisible(True)
            self.pdf_info.setVisible(False)
            return
        self.drop_zone.setVisible(False)
        self.pdf_info.setVisible(True)
        self.pdf_name_lbl.setText(f"📄  {self._pdf_path.name}")
        if self._page_count:
            self.pdf_meta_lbl.setText(self.i18n.t("pdf_pages_label", n=self._page_count))
        else:
            self.pdf_meta_lbl.setText("")

    def _pick_csv(self) -> None:
        suggested = ""
        if self._pdf_path:
            suggested = str(self._pdf_path.with_suffix(".csv"))
        path, _ = QFileDialog.getSaveFileName(
            self, self.i18n.t("dlg_csv_title"), suggested,
            self.i18n.t("dlg_csv_filter"),
        )
        if path:
            self.csv_edit.setText(path)

    def _pick_exclude(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, self.i18n.t("dlg_exclude_title"), "",
            self.i18n.t("dlg_txt_filter"),
        )
        if path:
            self._exclude_path = Path(path)
            self.exclude_label.setText(f"📄  {self._exclude_path.name}")

    def _clear_exclude(self) -> None:
        self._exclude_path = None
        self.exclude_label.setText(self.i18n.t("exclude_none"))

    def _open_output_folder(self) -> None:
        target = Path(self.csv_edit.text()).parent if self.csv_edit.text().strip() \
            else Path.home()
        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        try:
            if platform.system() == "Darwin":
                subprocess.Popen(["open", str(target)])
            elif platform.system() == "Windows":
                os.startfile(str(target))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(target)])
        except Exception:
            pass

    # ---------------------------- extraction ---------------------------- #

    def _gather_options(self) -> Optional[ExtractOptions]:
        if self._pdf_path is None:
            QMessageBox.information(self, self.i18n.t("app_title"),
                                    self.i18n.t("msg_select_pdf"))
            return None

        csv_path_str = self.csv_edit.text().strip() or str(self._pdf_path.with_suffix(".csv"))
        csv_path = Path(csv_path_str).expanduser()

        if self.all_pages_chk.isChecked():
            start, end = 1, None
        else:
            start = max(1, self.start_spin.value())
            end_val = self.end_spin.value()
            end = end_val if end_val > 0 else None

        pos_filter = {k for k, p in self.pos_pills.items() if p.isChecked()}
        if not pos_filter:
            pos_filter = {"noun"}

        return ExtractOptions(
            pdf_path=self._pdf_path,
            csv_path=csv_path,
            page_start=start,
            page_end=end,
            pos_filter=pos_filter,
            remove_proper_nouns=self.chk_proper.isChecked(),
            remove_basic_words=self.chk_basic.isChecked(),
            custom_exclude_path=self._exclude_path,
            min_length=self.min_len_spin.value(),
            min_frequency=self.min_freq_spin.value(),
            sort_by=self.sort_combo.currentData() or "frequency",
            include_frequency=self.chk_inc_freq.isChecked(),
            include_pos=self.chk_inc_pos.isChecked(),
            export_mode=self.export_combo.currentData() or "single_csv",
            reading_mode=self.reading_combo.currentData() or "auto",
        )

    def _on_extract_clicked(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        opts = self._gather_options()
        if opts is None:
            return

        self.action_btn.setText(self.i18n.t("action_extracting"))
        self.action_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.cancel_btn.setEnabled(True)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self._set_status(self.i18n.t("status_working"), state="working")
        self._set_log("", "info")

        self._worker = ExtractWorker(opts)
        self._worker.progress.connect(lambda p: self.progress.setValue(int(p * 1000)))
        self._worker.stage.connect(self._on_stage)
        self._worker.finished_ok.connect(self._on_extract_done)
        self._worker.failed.connect(self._on_extract_error)
        self._worker.cancelled.connect(self._on_extract_cancelled)
        self._worker.start()

    def _on_stage(self, stage: str) -> None:
        """Update status chip + log when the extractor signals a phase change."""
        key_map = {
            "ocr_init": "status_ocr_init",
            "ocr_running": "status_ocr_running",
        }
        key = key_map.get(stage)
        if key:
            text = self.i18n.t(key)
            self._set_status(text, state="working")
            self._set_log(text, state="info")

    def _on_cancel_clicked(self) -> None:
        if self._worker is None:
            return
        self.cancel_btn.setEnabled(False)
        self._worker.cancel()

    def _on_extract_done(self, result: ExtractResult) -> None:
        self._reset_action_state()
        self._set_status(self.i18n.t("status_done"), state="done")
        self.progress.setValue(1000)
        if not result.rows:
            # Be specific about WHY: the most useful signal is whether the PDF
            # had any Cyrillic text at all.
            if result.cyrillic_chars == 0:
                key = "msg_no_cyrillic"
            elif result.raw_tokens == 0:
                # Cyrillic chars exist but no 2+ letter words — odd encoding.
                key = "msg_no_tokens"
            else:
                # Words existed but were filtered out entirely.
                key = "msg_all_filtered"
            self._set_log(self.i18n.t(key), state="error")
            return
        primary = result.output_paths[0] if result.output_paths else self._csv_path
        self._set_log(
            self.i18n.t("msg_done", n=len(result.rows), path=str(primary)),
            state="success",
        )

    def _on_extract_cancelled(self) -> None:
        self._reset_action_state()
        self._set_status(self.i18n.t("status_ready"), state="ready")
        self.progress.setVisible(False)
        self._set_log(self.i18n.t("msg_cancelled"), state="info")

    def _on_extract_error(self, message: str) -> None:
        self._reset_action_state()
        self._set_status(self.i18n.t("status_error"), state="error")
        self.progress.setVisible(False)
        # Translate ExtractError keys we encoded.
        if message.startswith("__KEY__:"):
            try:
                _, key, fmt_repr = message.split(":", 2)
                fmt = eval(fmt_repr) if fmt_repr.strip().startswith("{") else {}
                message = self.i18n.t(key, **fmt)
            except Exception:
                pass
        self._set_log(self.i18n.t("msg_error", err=message), state="error")

    def _reset_action_state(self) -> None:
        self.action_btn.setText(self.i18n.t("action_extract"))
        self.action_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self._worker = None

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
        super().closeEvent(event)


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #


def main() -> int:
    app = QApplication(sys.argv)

    # System fonts: prefer SF Pro on macOS, Segoe UI on Windows.
    family = "SF Pro Text" if platform.system() == "Darwin" else "Segoe UI"
    if family in QFontDatabase.families():
        app.setFont(QFont(family, 10))

    app.setStyleSheet(STYLESHEET)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
