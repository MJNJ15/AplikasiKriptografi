"""Tab Gambar: steganografi LSB (sisip & ekstrak) — §4.8.

Wajib format PNG (lossless). Kata sandi dipakai sebagai kunci permutasi.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.stego import embed_message, extract_message

PNG_FILTER = "PNG (*.png)"


class ImageTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._cover_path: Optional[Path] = None

        self.cover_label = QLabel("Belum ada gambar penutup dipilih.")
        self.message_edit = QPlainTextEdit()
        self.message_edit.setPlaceholderText("Pesan yang disisipkan / hasil ekstraksi…")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Kata sandi (kunci permutasi)")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.choose_btn = QPushButton("Pilih Gambar…")
        self.embed_btn = QPushButton("Sisip Pesan")
        self.extract_btn = QPushButton("Ekstrak Pesan")
        self.status_label = QLabel("Siap.")

        self.choose_btn.clicked.connect(self._on_choose)
        self.embed_btn.clicked.connect(self._on_embed)
        self.extract_btn.clicked.connect(self._on_extract)

        row = QHBoxLayout()
        row.addWidget(self.choose_btn)
        row.addWidget(self.embed_btn)
        row.addWidget(self.extract_btn)
        row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.cover_label)
        layout.addWidget(self.message_edit)
        layout.addWidget(QLabel("Kata sandi:"))
        layout.addWidget(self.password_edit)
        layout.addLayout(row)
        layout.addWidget(self.status_label)

    def _key_bytes(self) -> bytes:
        return self.password_edit.text().encode("utf-8")

    def _on_choose(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Pilih gambar penutup (PNG)", "", PNG_FILTER)
        if path:
            self._cover_path = Path(path)
            self.cover_label.setText(f"Gambar: {self._cover_path.name}")

    def _on_embed(self) -> None:
        if self._cover_path is None or not self._cover_path.exists():
            QMessageBox.warning(self, "Gambar", "Pilih gambar penutup lebih dulu.")
            return
        message = self.message_edit.toPlainText().encode("utf-8")
        if not message:
            QMessageBox.warning(self, "Gambar", "Pesan kosong.")
            return
        cover = cv2.imread(str(self._cover_path))
        if cover is None:
            QMessageBox.warning(self, "Gambar", "Gagal membaca gambar.")
            return
        try:
            stego = embed_message(cover, message, self._key_bytes())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Sisip gagal", str(exc))
            return
        default = str(self._cover_path.with_name(self._cover_path.stem + "_stego.png"))
        dst, _ = QFileDialog.getSaveFileName(self, "Simpan gambar stego", default, PNG_FILTER)
        if not dst:
            return
        ok = cv2.imwrite(dst, stego)
        self.status_label.setText(
            f"Tersimpan: {Path(dst).name}" if ok else "Gagal menyimpan gambar."
        )

    def _on_extract(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Pilih gambar stego (PNG)", "", PNG_FILTER)
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            QMessageBox.warning(self, "Gambar", "Gagal membaca gambar.")
            return
        try:
            message = extract_message(img, self._key_bytes())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Ekstrak gagal", str(exc))
            return
        self.message_edit.setPlainText(message.decode("utf-8"))
        self.status_label.setText("Ekstraksi berhasil.")
