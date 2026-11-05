"""Tab File: enkripsi/dekripsi ChaCha20-Poly1305 — §4.5.

Kriteria 4: file dienkripsi dengan kriptografi berbeda dari teks.
Input via dialog file standar; hasil ditulis ke disk langsung.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.file_crypto import decrypt_file, encrypt_file

ENC_SUFFIX = ".enc"


class FileTab(QWidget):
    def __init__(self, chacha_key: bytes, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._key = chacha_key
        self._src_path: Optional[Path] = None

        self.file_label = QLabel("Belum ada file dipilih.")
        self.open_btn = QPushButton("Pilih File…")
        self.encrypt_btn = QPushButton("Enkripsi File")
        self.decrypt_btn = QPushButton("Dekripsi File")
        self.status_label = QLabel("Siap.")

        self.open_btn.clicked.connect(self._on_open)
        self.encrypt_btn.clicked.connect(self._on_encrypt)
        self.decrypt_btn.clicked.connect(self._on_decrypt)

        row = QHBoxLayout()
        row.addWidget(self.open_btn)
        row.addWidget(self.encrypt_btn)
        row.addWidget(self.decrypt_btn)
        row.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.file_label)
        layout.addLayout(row)
        layout.addWidget(self.status_label)

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Pilih file untuk diproses")
        if path:
            self._src_path = Path(path)
            self.file_label.setText(f"File: {self._src_path.name}")

    def _on_encrypt(self) -> None:
        if self._src_path is None or not self._src_path.exists():
            QMessageBox.warning(self, "File", "Pilih file lebih dulu.")
            return
        dst = Path(str(self._src_path) + ENC_SUFFIX)
        try:
            encrypt_file(self._src_path, dst, self._key)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Enkripsi gagal", str(exc))
            return
        self.status_label.setText(f"Tersimpan: {dst.name}")

    def _on_decrypt(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Pilih file terenkripsi (.enc)", "", f"Enkripsi ({ENC_SUFFIX})"
        )
        if not path:
            return
        src = Path(path)
        dst = src.with_name(src.name.removesuffix(ENC_SUFFIX) or (src.name + ".dec"))
        try:
            decrypt_file(src, dst, self._key)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Dekripsi gagal", str(exc))
            return
        self.status_label.setText(f"Hasil dekripsi: {dst.name}")
