"""Tab File: enkripsi/dekripsi ChaCha20-Poly1305 — §4.5.

Dipisah menjadi dua sub-tab: "Enkripsi" dan "Dekripsi". Tiap panel:
tombol pilih file di kiri atas → preview (teks/gambar/metadata) →
aksi rata kanan. Kunci memakai turunan kunci sesi (lihat MainWindow).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal, Optional

import cv2

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.file_crypto import decrypt_file, encrypt_file

ENC_SUFFIX = ".enc"
PREVIEW_WIDTH = 360
PREVIEW_HEIGHT = 240
TEXT_PREVIEW_LINES = 50

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
TEXT_EXTS = {
    ".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml",
    ".py", ".js", ".html", ".css", ".sql", ".log", ".ini", ".cfg", ".bat",
}


def _human_size(nbytes: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.0f} {unit}" if unit == "B" else f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def _text_preview(path: Path, max_lines: int = TEXT_PREVIEW_LINES) -> str:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    lines = text.splitlines()
    shown = lines[:max_lines]
    preview = "\n".join(shown)
    if len(lines) > max_lines:
        preview += f"\n… ({len(lines) - max_lines} baris lagi)"
    return preview


class FilePanel(QWidget):
    """Panel enkripsi ATAU dekripsi file."""

    def __init__(self, mode: Literal["encrypt", "decrypt"], chacha_key: bytes, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.mode = mode
        self._key = chacha_key
        self._path: Optional[Path] = None

        # Tombol pilih file — kiri atas
        self.choose_btn = QPushButton("Pilih File…")
        self.choose_btn.setObjectName("chooseBtn")
        self.choose_btn.clicked.connect(self._on_choose)

        top_row = QHBoxLayout()
        top_row.addWidget(self.choose_btn)
        top_row.addStretch(1)

        self.info_label = QLabel("Belum ada file dipilih.")
        self.info_label.setWordWrap(True)

        self.image_preview = QLabel("–")
        self.image_preview.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet(
            "background:#1a1e27; color:#8a94a8; border-radius:8px;"
        )
        self.image_preview.hide()

        self.text_preview = QPlainTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.hide()

        self.meta_label = QLabel("")
        self.meta_label.setWordWrap(True)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.clicked.connect(self._on_reset)

        self.action_btn = QPushButton("Enkripsi File" if mode == "encrypt" else "Dekripsi File")
        self.action_btn.clicked.connect(self._on_action)
        self.status_label = QLabel("Siap.")

        # Aksi rata kanan; reset di samping kirinya
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.reset_btn)
        row.addWidget(self.action_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addWidget(self.info_label)
        layout.addWidget(self.image_preview)
        layout.addWidget(self.text_preview)
        layout.addWidget(self.meta_label)
        layout.addLayout(row)
        layout.addWidget(self.status_label)

    def _on_choose(self) -> None:
        is_decrypt = self.mode == "decrypt"
        flt = f"Enkripsi ({ENC_SUFFIX});;Semua file (*)" if is_decrypt else "Semua file (*)"
        path, _ = QFileDialog.getOpenFileName(self, "Pilih file", "", flt)
        if not path:
            return
        self._path = Path(path)
        self._show_preview()

    def _show_preview(self) -> None:
        assert self._path is not None
        path = self._path
        ext = path.suffix.lower()
        self.info_label.setText(
            f"File: {path.name} — {_human_size(path.stat().st_size)}"
        )
        self.image_preview.hide()
        self.text_preview.hide()
        self.meta_label.setText("")

        if ext in IMAGE_EXTS:
            img = cv2.imread(str(path))
            if img is not None:
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
                self.image_preview.setPixmap(
                    QPixmap.fromImage(qimg).scaled(
                        self.image_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.image_preview.show()
                self.status_label.setText("Preview gambar ditampilkan.")
                return
        elif ext in TEXT_EXTS:
            self.text_preview.setPlainText(_text_preview(path))
            self.text_preview.show()
            self.status_label.setText("Preview teks ditampilkan.")
            return

        # Tidak dapat dipratinjau / file terenkripsi
        if ext == ENC_SUFFIX:
            self.meta_label.setText("File terenkripsi — konten tidak dapat dipratinjau.")
        else:
            self.meta_label.setText("File biner — hanya metadata:")
            self.meta_label.setText(
                self.meta_label.text()
                + f"\nSHA-256: {_sha256_file(path)}"
            )
        self.status_label.setText("Preview tidak tersedia untuk jenis file ini.")

    def _on_reset(self) -> None:
        self._path = None
        self.info_label.setText("Belum ada file dipilih.")
        self.image_preview.hide()
        self.text_preview.hide()
        self.meta_label.setText("")
        self.status_label.setText("Semua input dibersihkan.")

    def _on_action(self) -> None:
        if self._path is None or not self._path.exists():
            QMessageBox.warning(self, "File", "Pilih file lebih dulu.")
            return
        try:
            if self.mode == "encrypt":
                dst = Path(str(self._path) + ENC_SUFFIX)
                encrypt_file(self._path, dst, self._key)
                self.status_label.setText(f"Tersimpan: {dst.name}")
            else:
                src = self._path
                dst = src.with_name(
                    src.name.removesuffix(ENC_SUFFIX) or (src.name + ".dec")
                )
                decrypt_file(src, dst, self._key)
                self.status_label.setText(f"Hasil dekripsi: {dst.name}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Gagal", str(exc))


class FileTab(QWidget):
    """Tab utama berisi sub-tab Enkripsi & Dekripsi file."""

    def __init__(self, chacha_key: bytes, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.encrypt_panel = FilePanel("encrypt", chacha_key)
        self.decrypt_panel = FilePanel("decrypt", chacha_key)

        tabs = QTabWidget()
        tabs.addTab(self.encrypt_panel, "Enkripsi")
        tabs.addTab(self.decrypt_panel, "Dekripsi")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)
