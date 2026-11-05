"""Tab Teks: super enkripsi (klasik → modern) — §4.4.

Memakai `TextTab` dengan callback `text_keys_provider` (kunci sesi) sebagai
default. Jika kolom "Kunci kustom" diisi, kunci itulah yang dipakai
(lihat keys.keys_from_custom). Tombol aksi rata kanan.
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.keys import keys_from_custom
from ..core.super_encrypt import decrypt_text, encrypt_text


class TextTab(QWidget):
    def __init__(
        self,
        text_keys_provider: Callable[[], tuple[bytes, bytes, bytes]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._keys_provider = text_keys_provider

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("Pesan teks polos…")
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Hasil (Base64) akan tampil di sini…")
        self.status_label = QLabel("Siap.")

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Kunci kustom (opsional — kosongkan utk kunci sesi)")
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.encrypt_btn = QPushButton("Enkripsi")
        self.decrypt_btn = QPushButton("Dekripsi")
        self.encrypt_btn.clicked.connect(self._on_encrypt)
        self.decrypt_btn.clicked.connect(self._on_decrypt)

        # Tombol menempel ke kanan
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.encrypt_btn)
        btn_row.addWidget(self.decrypt_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Teks masukan:"))
        layout.addWidget(self.input_edit)
        layout.addWidget(QLabel("Kunci kustom (opsional):"))
        layout.addWidget(self.key_edit)
        layout.addLayout(btn_row)
        layout.addWidget(QLabel("Hasil:"))
        layout.addWidget(self.output_edit)
        layout.addWidget(self.status_label)

    def _keys(self) -> tuple[bytes, bytes, bytes]:
        custom = self.key_edit.text()
        if custom.strip():
            return keys_from_custom(custom.encode("utf-8"))
        return self._keys_provider()

    def _on_encrypt(self) -> None:
        text = self.input_edit.toPlainText()
        if not text:
            self.status_label.setText("Masukan kosong.")
            return
        try:
            blob = encrypt_text(text, *self._keys())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Enkripsi gagal", str(exc))
            return
        self.output_edit.setPlainText(blob)
        self.status_label.setText("Enkripsi berhasil.")

    def _on_decrypt(self) -> None:
        blob = self.output_edit.toPlainText()
        if not blob:
            self.status_label.setText("Belum ada hasil untuk didekripsi.")
            return
        try:
            text = decrypt_text(blob, *self._keys())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Dekripsi gagal", str(exc))
            return
        self.input_edit.setPlainText(text)
        self.status_label.setText("Dekripsi berhasil.")
