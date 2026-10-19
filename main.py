"""
CitrusDrop — main application window.

A local-first file converter for Ubuntu.  All processing happens on your
machine; nothing is uploaded.
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QComboBox, QFileDialog,
    QMessageBox, QFrame, QProgressBar, QDialog, QGridLayout,
)

import converter

APP_NAME = "CitrusDrop"
OUTPUT_DIR = Path.home() / "CitrusDrop"


# ── Worker thread for conversions ─────────────────────────────────────────

class _ConvertSignals(QObject):
    """Signals emitted by the conversion worker."""
    progress = Signal(int, int)          # (current_index, total)
    file_done = Signal(str, bool, str)   # (filename, success, message)
    finished = Signal(int, list)         # (succeeded, failed_messages)


class ConvertWorker(QThread):
    """Runs conversion jobs off the main thread so the UI stays responsive."""

    def __init__(self, files: list[str], fmt: str, output_dir: Path, parent=None):
        super().__init__(parent)
        self.files = files
        self.fmt = fmt
        self.output_dir = output_dir
        self.signals = _ConvertSignals()

    def run(self):
        succeeded = 0
        failed: list[str] = []
        total = len(self.files)

        for i, raw in enumerate(self.files):
            src = Path(raw)
            name = src.name
            try:
                # Validate before converting.
                err = converter.validate_conversion(src, self.fmt)
                if err:
                    raise RuntimeError(err)

                dest = self.output_dir / f"{src.stem}.{self.fmt}"
                dest = converter.unique_path(dest)

                if self.fmt in converter.IMAGE_FORMATS:
                    converter.convert_image(src, dest, self.fmt)
                elif self.fmt in converter.MEDIA_FORMATS:
                    converter.convert_media(src, dest)
                else:
                    raise RuntimeError(
                        f"'{self.fmt.upper()}' is not supported by the current prototype."
                    )

                succeeded += 1
                self.signals.file_done.emit(name, True, str(dest))
            except Exception as exc:
                failed.append(f"{name}: {exc}")
                self.signals.file_done.emit(name, False, str(exc))

            self.signals.progress.emit(i + 1, total)

        self.signals.finished.emit(succeeded, failed)


# ── Drop zone ─────────────────────────────────────────────────────────────

class DropZone(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label = QLabel("＋")
        self.icon_label.setObjectName("DropIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel("Drop files here")
        self.title_label.setObjectName("DropTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle = QLabel("or choose files from your computer")
        self.subtitle.setObjectName("Muted")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.browse_button = QPushButton("Choose files")
        self.browse_button.setObjectName("AccentButton")
        layout.addWidget(self.icon_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle)
        layout.addSpacing(8)
        layout.addWidget(self.browse_button, alignment=Qt.AlignmentFlag.AlignCenter)
        self.on_files = None
        self.browse_button.clicked.connect(self.browse)

    def browse(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose files")
        if paths and self.on_files:
            self.on_files(paths)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths and self.on_files:
            self.on_files(paths)
        event.acceptProposedAction()


# ── Radial format picker ─────────────────────────────────────────────────

class RadialPicker(QDialog):
    """Small, self-contained radial format picker prototype."""

    def __init__(self, parent=None, current="PNG"):
        super().__init__(parent)
        self.setWindowTitle("Quick format")
        self.setModal(True)
        self.setFixedSize(340, 340)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.current = current
        self.selected = current
        # Only formats that are actually implemented.
        self.formats = ["PNG", "JPG", "WEBP", "MP3", "MP4", "WAV"]
        self.setStyleSheet("""
            QDialog { background: transparent; }
            QPushButton {
                background: #24252b; color: #f4f4f5; border: 1px solid #444650;
                border-radius: 25px; min-width: 74px; min-height: 48px;
                font-weight: 600; font-size: 12px;
            }
            QPushButton:hover { background: #ff9f43; color: #1d1d20; border-color: #ff9f43; }
        """)
        grid = QGridLayout(self)
        grid.setContentsMargins(34, 34, 34, 34)
        grid.setSpacing(10)
        positions = [(0, 1), (0, 2), (1, 2), (2, 1), (2, 0), (1, 0)]
        for fmt, pos in zip(self.formats, positions):
            btn = QPushButton(fmt)
            btn.clicked.connect(lambda checked=False, f=fmt: self.choose(f))
            grid.addWidget(btn, *pos)
        center = QLabel("CITRUS\nDROP")
        center.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.setStyleSheet(
            "background:#ff9f43;color:#1d1d20;border-radius:42px;font-weight:800;"
        )
        center.setFixedSize(84, 84)
        grid.addWidget(center, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)

    def choose(self, fmt):
        self.selected = fmt
        self.accept()


# ── Main window ───────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CitrusDrop")
        self.resize(940, 720)
        self.setMinimumSize(760, 620)
        self.files: list[str] = []
        self._worker: ConvertWorker | None = None
        self.setAcceptDrops(True)

        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        # ── Header ──
        header = QHBoxLayout()
        brand = QHBoxLayout()
        logo = QLabel("✳")
        logo.setObjectName("Logo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(42, 42)
        brand_text = QVBoxLayout()
        name = QLabel("CitrusDrop")
        name.setObjectName("Brand")
        tagline = QLabel("A little file magic. All on your machine.")
        tagline.setObjectName("Muted")
        brand_text.addWidget(name)
        brand_text.addWidget(tagline)
        brand.addWidget(logo)
        brand.addLayout(brand_text)
        header.addLayout(brand)
        header.addStretch()
        self.quick_button = QPushButton("✣  Quick format")
        self.quick_button.setObjectName("SecondaryButton")
        self.quick_button.clicked.connect(self.open_radial)
        header.addWidget(self.quick_button)
        outer.addLayout(header)

        # ── Hero ──
        hero = QVBoxLayout()
        title = QLabel("Convert anything, simply.")
        title.setObjectName("HeroTitle")
        desc = QLabel("Drop your files, pick a format, and keep your files private.")
        desc.setObjectName("Muted")
        hero.addWidget(title)
        hero.addWidget(desc)
        outer.addLayout(hero)

        # ── Drop zone ──
        self.dropzone = DropZone()
        self.dropzone.on_files = self.add_files
        outer.addWidget(self.dropzone)

        # ── File list header ──
        row = QHBoxLayout()
        section = QLabel("YOUR FILES")
        section.setObjectName("SectionLabel")
        self.file_count = QLabel("0 files")
        self.file_count.setObjectName("Muted")
        row.addWidget(section)
        row.addStretch()
        row.addWidget(self.file_count)
        outer.addLayout(row)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("FileList")
        self.list_widget.setMinimumHeight(110)
        outer.addWidget(self.list_widget, 1)

        # ── Controls ──
        controls = QHBoxLayout()
        left = QVBoxLayout()
        fmt_label = QLabel("OUTPUT FORMAT")
        fmt_label.setObjectName("SectionLabel")
        self.format_combo = QComboBox()
        self.format_combo.addItems(
            ["PNG", "JPG", "WEBP", "BMP", "TIFF",
             "MP3", "WAV", "OGG", "MP4", "WEBM", "MKV"]
        )
        self.format_combo.setMinimumWidth(160)
        left.addWidget(fmt_label)
        left.addWidget(self.format_combo)
        controls.addLayout(left)
        controls.addStretch()
        self.clear_button = QPushButton("Clear list")
        self.clear_button.setObjectName("SecondaryButton")
        self.clear_button.clicked.connect(self.clear_files)
        controls.addWidget(self.clear_button, alignment=Qt.AlignmentFlag.AlignBottom)
        self.convert_button = QPushButton("Convert files  →")
        self.convert_button.setObjectName("AccentButton")
        self.convert_button.setMinimumHeight(44)
        self.convert_button.setMinimumWidth(180)
        self.convert_button.clicked.connect(self.convert_files)
        controls.addWidget(self.convert_button, alignment=Qt.AlignmentFlag.AlignBottom)
        outer.addLayout(controls)

        # ── Progress ──
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        self.progress.setValue(0)
        outer.addWidget(self.progress)

        self.status = QLabel("Ready • Files are processed locally")
        self.status.setObjectName("Muted")
        outer.addWidget(self.status)

        self.setStyleSheet(_STYLESHEET)

    # ── File management ──────────────────────────────────────────────────

    def add_files(self, paths: list[str]) -> None:
        added = 0
        for raw in paths:
            path = Path(raw).expanduser().resolve()
            if path.is_file() and str(path) not in self.files:
                self.files.append(str(path))
                try:
                    size_str = converter.human_size(path.stat().st_size)
                except OSError:
                    size_str = "? B"
                item = QListWidgetItem(f"  ◇   {path.name}     ·     {size_str}")
                item.setToolTip(str(path))
                self.list_widget.addItem(item)
                added += 1
        self.file_count.setText(
            f"{len(self.files)} file{'s' if len(self.files) != 1 else ''}"
        )
        if added:
            self.status.setText(f"Added {added} file(s) • Nothing leaves your computer")

    def clear_files(self) -> None:
        self.files.clear()
        self.list_widget.clear()
        self.file_count.setText("0 files")
        self.progress.setValue(0)
        self.status.setText("Ready • Files are processed locally")

    # ── Radial picker ────────────────────────────────────────────────────

    def open_radial(self) -> None:
        picker = RadialPicker(self, self.format_combo.currentText())
        if picker.exec() == QDialog.DialogCode.Accepted:
            fmt = picker.selected
            idx = self.format_combo.findText(fmt)
            if idx < 0:
                self.format_combo.addItem(fmt)
                idx = self.format_combo.findText(fmt)
            self.format_combo.setCurrentIndex(idx)

    # ── Conversion ───────────────────────────────────────────────────────

    def convert_files(self) -> None:
        if not self.files:
            QMessageBox.information(
                self, "No files selected",
                "Drop some files into CitrusDrop first."
            )
            return

        if self._worker is not None and self._worker.isRunning():
            QMessageBox.information(
                self, "Conversion in progress",
                "Please wait for the current conversion to finish."
            )
            return

        fmt = self.format_combo.currentText().lower()
        output_dir = OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        self.progress.setValue(0)
        self.convert_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.status.setText("Converting…")

        self._worker = ConvertWorker(list(self.files), fmt, output_dir, parent=self)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, current: int, total: int) -> None:
        self.progress.setValue(int(current * 100 / max(total, 1)))
        self.status.setText(f"Converting… {current}/{total}")

    def _on_finished(self, succeeded: int, failed: list[str]) -> None:
        self.convert_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self._worker = None

        message = f"Finished: {succeeded} converted.\nOutput folder: {OUTPUT_DIR}"
        if failed:
            message += "\n\nCould not convert:\n" + "\n".join(failed[:12])

        self.status.setText(f"{succeeded} converted • Saved to ~/CitrusDrop")
        QMessageBox.information(self, "Conversion results", message)


# ── Stylesheet ────────────────────────────────────────────────────────────

_STYLESHEET = """
QWidget#Root {
    background: #15161a; color: #f4f4f5;
    font-family: Inter, 'Ubuntu', sans-serif;
}
QLabel { color: #f4f4f5; }
QLabel#Logo {
    background: #ff9f43; color: #191a1e;
    border-radius: 13px; font-size: 26px; font-weight: 900;
}
QLabel#Brand   { font-size: 20px; font-weight: 800; }
QLabel#HeroTitle { font-size: 29px; font-weight: 750; }
QLabel#Muted   { color: #999ba6; font-size: 12px; }
QLabel#SectionLabel { color: #a7a9b4; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
QLabel#DropIcon  { color: #ff9f43; font-size: 34px; font-weight: 300; }
QLabel#DropTitle { font-size: 18px; font-weight: 700; }
QFrame#DropZone {
    background: #1c1d22; border: 2px dashed #41434c; border-radius: 18px;
}
QFrame#DropZone[dragging="true"] {
    background: #29231e; border-color: #ff9f43;
}
QListWidget#FileList {
    background: #1b1c21; border: 1px solid #303139;
    border-radius: 12px; padding: 7px; outline: 0;
}
QListWidget::item { padding: 10px; border-bottom: 1px solid #2a2b31; }
QListWidget::item:selected { background: #30271f; color: #ffbd7c; }
QComboBox {
    background: #24252b; color: #f4f4f5;
    border: 1px solid #3a3b44; border-radius: 9px; padding: 10px 12px;
}
QComboBox QAbstractItemView {
    background: #24252b; color: #f4f4f5;
    selection-background-color: #ff9f43; selection-color: #191a1e;
}
QPushButton {
    border: 0; border-radius: 10px; padding: 11px 15px; font-weight: 650;
}
QPushButton#AccentButton {
    background: #ff9f43; color: #20170f;
}
QPushButton#AccentButton:hover { background: #ffb15f; }
QPushButton#AccentButton:disabled { background: #5e4d38; color: #908070; }
QPushButton#SecondaryButton {
    background: #25262c; color: #e7e7eb; border: 1px solid #3a3b43;
}
QPushButton#SecondaryButton:hover { background: #303139; }
QProgressBar {
    background: #2b2c32; border: 0; border-radius: 2px;
}
QProgressBar::chunk { background: #ff9f43; border-radius: 2px; }
"""


# ── Entry point ───────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
