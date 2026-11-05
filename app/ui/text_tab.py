"""Tab Teks: super enkripsi (klasik → modern) — §4.4.

Dipisah menjadi dua sub-tab: "Enkripsi" dan "Dekripsi". Setiap sub-tab
punya kolom kunci per-algoritma tersendiri (wajib diisi): Vigenère, Caesar,
LFSR (seed), DES, HMAC. Tombol aksi rata kanan.
"""

from __future__ import annotations

from typing import Literal, Optional

from PySide6.QtWidgets import (
    QGridLayout,
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

from ..core.keys import TextKeys, derive_des_key
from ..core.super_encrypt import decrypt_text, encrypt_text


class CryptoPanel(QWidget):
    """Panel enkripsi ATAU dekripsi (dipakai di dalam sub-tab)."""

    def __init__(self, mode: Literal["encrypt", "decrypt"], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.mode = mode
        is_encrypt = mode == "encrypt"

        self.input_edit = QPlainTextEdit()
        self.input_edit.setPlaceholderText(
            "Pesan teks polos…" if is_encrypt else "Tempel ciphertext (Base64)…"
        )
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText(
            "Hasil (Base64)…" if is_encrypt else "Hasil teks polos…"
        )
        self.status_label = QLabel("Siap.")
        self._key_error = ""

        self.vigenere_edit = self._key_line("Kunci Vigenère (huruf/kata)")
        self.caesar_edit = self._key_line("Kunci Caesar (shift/kata)")
        self.lfsr_edit = self._key_line("Kunci LFSR — seed (min. 4 karakter)")
        self.des_edit = self._key_line("Kunci DES (8 karakter; selain itu di-hash)")
        self.mac_edit = self._key_line("Kunci HMAC-SHA256")

        self.action_btn = QPushButton("Enkripsi" if is_encrypt else "Dekripsi")
        self.action_btn.clicked.connect(self._on_action)

        self.clear_input_btn = QPushButton("Bersihkan Input")
        self.clear_input_btn.setObjectName("secondaryBtn")
        self.clear_input_btn.clicked.connect(self._on_clear_input)

        # Tombol menempel ke kanan
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.clear_input_btn)
        btn_row.addWidget(self.action_btn)

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
        layout.addWidget(QLabel("Masukan:"))
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

    def _on_action(self) -> None:
        payload = self.input_edit.toPlainText()
        if not payload:
            self.status_label.setText("Masukan kosong.")
            return
        keys = self._parse_keys()
        if keys is None:
            self.status_label.setText(self._key_error)
            return
        try:
            if self.mode == "encrypt":
                result = encrypt_text(payload, keys)
                success_msg = "Enkripsi berhasil."
            else:
                result = decrypt_text(payload, keys)
                success_msg = "Dekripsi berhasil."
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Gagal", str(exc))
            return
        self.output_edit.setPlainText(result)
        self.status_label.setText(success_msg)

    def _on_clear_input(self) -> None:
        """Bersihkan kolom masukan saja (kunci & hasil tetap)."""
        self.input_edit.clear()
        self.status_label.setText("Input dibersihkan.")


class TextTab(QWidget):
    """Tab utama berisi sub-tab Enkripsi & Dekripsi."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.encrypt_panel = CryptoPanel("encrypt")
        self.decrypt_panel = CryptoPanel("decrypt")

        tabs = QTabWidget()
        tabs.addTab(self.encrypt_panel, "Enkripsi")
        tabs.addTab(self.decrypt_panel, "Dekripsi")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)
