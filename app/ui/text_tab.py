"""Tab Teks: super enkripsi (klasik → modern) — §4.4.

Setiap algoritma punya kolom kunci tersendiri (wajib diisi):
Vigenère, Caesar, LFSR (seed), DES, HMAC. Tombol aksi rata kanan.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core.keys import TextKeys, derive_des_key
from ..core.super_encrypt import decrypt_text, encrypt_text


class TextTab(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText("Pesan teks polos…")
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Hasil (Base64) akan tampil di sini…")
        self.status_label = QLabel("Siap.")
        self._key_error = ""

        # Kolom kunci per-algoritma (wajib diisi)
        self.vigenere_edit = self._key_line("Kunci Vigenère (huruf/kata)")
        self.caesar_edit = self._key_line("Kunci Caesar (shift/kata)")
        self.lfsr_edit = self._key_line("Kunci LFSR — seed (min. 4 karakter)")
        self.des_edit = self._key_line("Kunci DES (8 karakter; selain itu di-hash)")
        self.mac_edit = self._key_line("Kunci HMAC-SHA256")

        self.encrypt_btn = QPushButton("Enkripsi")
        self.decrypt_btn = QPushButton("Dekripsi")
        self.encrypt_btn.clicked.connect(self._on_encrypt)
        self.decrypt_btn.clicked.connect(self._on_decrypt)

        # Tombol menempel ke kanan
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.encrypt_btn)
        btn_row.addWidget(self.decrypt_btn)

        key_grid = QGridLayout()
        key_grid.setColumnStretch(1, 1)
        key_grid.addWidget(QLabel("Vigenère:"), 0, 0)
        key_grid.addWidget(self.vigenere_edit, 0, 1)
        key_grid.addWidget(QLabel("Caesar:"), 1, 0)
        key_grid.addWidget(self.caesar_edit, 1, 1)
        key_grid.addWidget(QLabel("LFSR:"), 2, 0)
        key_grid.addWidget(self.lfsr_edit, 2, 1)
        key_grid.addWidget(QLabel("DES:"), 3, 0)
        key_grid.addWidget(self.des_edit, 3, 1)
        key_grid.addWidget(QLabel("HMAC:"), 4, 0)
        key_grid.addWidget(self.mac_edit, 4, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Teks masukan:"))
        layout.addWidget(self.input_edit)
        layout.addWidget(QLabel("Kunci per algoritma (wajib):"))
        layout.addLayout(key_grid)
        layout.addLayout(btn_row)
        layout.addWidget(QLabel("Hasil:"))
        layout.addWidget(self.output_edit)
        layout.addWidget(self.status_label)

    @staticmethod
    def _key_line(placeholder: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setEchoMode(QLineEdit.EchoMode.Password)
        return edit

    def _parse_keys(self) -> Optional[TextKeys]:
        """Baca 5 kolom kunci; None bila ada yang kosong/tidak valid."""
        raw = {
            "vigenere": self.vigenere_edit.text(),
            "caesar": self.caesar_edit.text(),
            "lfsr": self.lfsr_edit.text(),
            "des": self.des_edit.text(),
            "mac": self.mac_edit.text(),
        }
        if any(not v.strip() for v in raw.values()):
            self._key_error = "Semua kolom kunci wajib diisi."
            return None
        if len(raw["lfsr"].strip()) < 4:
            self._key_error = "Kunci LFSR minimal 4 karakter."
            return None
        self._key_error = ""
        return TextKeys(
            vigenere=raw["vigenere"].encode("utf-8"),
            caesar=raw["caesar"].encode("utf-8"),
            lfsr=raw["lfsr"].encode("utf-8"),
            des=derive_des_key(raw["des"].encode("utf-8")),
            mac=raw["mac"].encode("utf-8"),
        )

    def _on_encrypt(self) -> None:
        text = self.input_edit.toPlainText()
        if not text:
            self.status_label.setText("Masukan kosong.")
            return
        keys = self._parse_keys()
        if keys is None:
            self.status_label.setText(self._key_error)
            return
        try:
            blob = encrypt_text(text, keys)
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
        keys = self._parse_keys()
        if keys is None:
            self.status_label.setText(self._key_error)
            return
        try:
            text = decrypt_text(blob, keys)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Dekripsi gagal", str(exc))
            return
        self.input_edit.setPlainText(text)
        self.status_label.setText("Dekripsi berhasil.")
