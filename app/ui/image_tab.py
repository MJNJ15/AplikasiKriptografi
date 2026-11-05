"""Tab Gambar: steganografi LSB (sisip & ekstrak) — §4.8.

Dipisah menjadi dua sub-tab: "Sisip Pesan" dan "Ekstrak Pesan".
Tiap panel: tombol pilih gambar di atas → preview gambar → isian pesan/
kata sandi → tombol aksi rata kanan. Wajib PNG (lossless).
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import cv2

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.stego import embed_message, extract_message

PNG_FILTER = "PNG (*.png)"
PREVIEW_WIDTH = 360
PREVIEW_HEIGHT = 240


class ImagePanel(QWidget):
    """Panel sisip ATAU ekstrak (dipakai di dalam sub-tab)."""

    def __init__(self, mode: Literal["embed", "extract"], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.mode = mode
        is_embed = mode == "embed"

        self._image_path: Optional[Path] = None
        self._image: Optional[object] = None

        # Tombol pilih gambar — kecil, di kiri
        self.choose_btn = QPushButton("Pilih Gambar…")
        self.choose_btn.setObjectName("smallBtn")
        self.choose_btn.clicked.connect(self._on_choose)

        top_row = QHBoxLayout()
        top_row.addWidget(self.choose_btn)
        top_row.addStretch(1)

        # Preview gambar yang dipilih
        self.preview_label = QLabel("Belum ada gambar dipilih.")
        self.preview_label.setFixedSize(PREVIEW_WIDTH, PREVIEW_HEIGHT)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(
            "background:#1a1e27; color:#8a94a8; border-radius:8px;"
        )

        self.message_edit = QPlainTextEdit()
        self.message_edit.setPlaceholderText(
            "Pesan yang disisipkan…" if is_embed else "Hasil pesan akan tampil di sini…"
        )
        if not is_embed:
            self.message_edit.setReadOnly(True)

        # Preview (kiri) + input pesan (kanan) dalam satu baris
        content_row = QHBoxLayout()
        content_row.addWidget(self.preview_label)
        content_row.addWidget(self.message_edit, 1)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Kata sandi (kunci permutasi)")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.action_btn = QPushButton("Sisip Pesan" if is_embed else "Ekstrak Pesan")
        self.action_btn.clicked.connect(self._on_action)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.clicked.connect(self._on_reset)

        # Tombol aksi rata kanan; reset di samping kirinya
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.reset_btn)
        row.addWidget(self.action_btn)

        self.status_label = QLabel("Siap.")

        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addLayout(content_row)
        layout.addWidget(QLabel("Kata sandi:"))
        layout.addWidget(self.password_edit)
        layout.addLayout(row)
        layout.addWidget(self.status_label)

    def _key_bytes(self) -> bytes:
        return self.password_edit.text().encode("utf-8")

    def _show_preview(self) -> None:
        if self._image is None:
            return
        rgb = cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        self.preview_label.setPixmap(
            QPixmap.fromImage(qimg).scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _on_choose(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Pilih gambar (PNG)", "", PNG_FILTER)
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            QMessageBox.warning(self, "Gambar", "Gagal membaca gambar.")
            return
        self._image_path = Path(path)
        self._image = img
        self._show_preview()
        self.status_label.setText(f"Gambar: {self._image_path.name}")

    def _on_reset(self) -> None:
        """Bersihkan kolom pesan saja (gambar & kata sandi tetap)."""
        self.message_edit.clear()
        self.status_label.setText("Pesan dibersihkan.")

    def _on_action(self) -> None:
        if self._image is None or self._image_path is None:
            QMessageBox.warning(self, "Gambar", "Pilih gambar lebih dulu.")
            return
        if not self.password_edit.text():
            self.status_label.setText("Kata sandi wajib diisi.")
            return
        try:
            if self.mode == "embed":
                message = self.message_edit.toPlainText().encode("utf-8")
                if not message:
                    QMessageBox.warning(self, "Gambar", "Pesan kosong.")
                    return
                stego = embed_message(self._image, message, self._key_bytes())
                default = str(
                    self._image_path.with_name(self._image_path.stem + "_stego.png")
                )
                dst, _ = QFileDialog.getSaveFileName(
                    self, "Simpan gambar stego", default, PNG_FILTER
                )
                if not dst:
                    return
                ok = cv2.imwrite(dst, stego)
                self.status_label.setText(
                    f"Tersimpan: {Path(dst).name}" if ok else "Gagal menyimpan gambar."
                )
            else:
                message = extract_message(self._image, self._key_bytes())
                self.message_edit.setPlainText(message.decode("utf-8"))
                self.status_label.setText("Ekstraksi berhasil.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Gagal", str(exc))


class ImageTab(QWidget):
    """Tab utama berisi sub-tab Sisip Pesan & Ekstrak Pesan."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.embed_panel = ImagePanel("embed")
        self.extract_panel = ImagePanel("extract")

        tabs = QTabWidget()
        tabs.addTab(self.embed_panel, "Sisip Pesan")
        tabs.addTab(self.extract_panel, "Ekstrak Pesan")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)
