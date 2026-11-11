"""Dialog pendaftaran akun baru (GUI).

Menggantikan pendaftaran berbasis terminal: username + kata sandi +
konfirmasi kata sandi. Setelah `accept()`, nilai diambil dari atribut
`username` dan `password`.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

CARD_WIDTH = 460


class RegisterDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Buat Akun Baru — Aplikasi Kriptografi")
        self.setFixedWidth(CARD_WIDTH)

        self.username: str = ""
        self.password: str = ""

        card = QFrame()
        card.setObjectName("loginCard")

        title = QLabel("Buat Akun Baru")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Daftarkan identitas untuk membuka aplikasi")
        subtitle.setObjectName("subtitleLabel")

        self.username_edit = QLineEdit()
        self.username_edit.setObjectName("inputField")
        self.username_edit.setPlaceholderText("contoh: budi")
        self.password_edit = QLineEdit()
        self.password_edit.setObjectName("inputField")
        self.password_edit.setPlaceholderText("••••••••")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setObjectName("inputField")
        self.confirm_edit.setPlaceholderText("••••••••")
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.status_label = QLabel("Isi data di bawah ini.")
        self.status_label.setObjectName("statusLabel")

        self.register_btn = QPushButton("Daftar")
        self.register_btn.setObjectName("primaryBtn")
        self.cancel_btn = QPushButton("Batal")
        self.cancel_btn.setObjectName("secondaryBtn")

        self.register_btn.clicked.connect(self._on_register)
        self.cancel_btn.clicked.connect(self.reject)
        self.confirm_edit.returnPressed.connect(self._on_register)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 36, 40, 36)
        card_layout.setSpacing(12)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(16)
        card_layout.addWidget(QLabel("Username"))
        card_layout.addWidget(self.username_edit)
        card_layout.addSpacing(6)
        card_layout.addWidget(QLabel("Kata sandi"))
        card_layout.addWidget(self.password_edit)
        card_layout.addSpacing(6)
        card_layout.addWidget(QLabel("Ulangi kata sandi"))
        card_layout.addWidget(self.confirm_edit)
        card_layout.addSpacing(18)
        card_layout.addWidget(self.register_btn)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_row.addWidget(self.cancel_btn)
        card_layout.addLayout(btn_row)

        card_layout.addSpacing(6)
        card_layout.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignHCenter)

        outer = QVBoxLayout(self)
        outer.addStretch(1)
        outer.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch(1)

    def _on_register(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        if not username:
            self.status_label.setText("Username wajib diisi.")
            return
        if not password:
            self.status_label.setText("Kata sandi wajib diisi.")
            return
        if len(password) < 6:
            self.status_label.setText("Kata sandi minimal 6 karakter.")
            return
        if password != confirm:
            self.status_label.setText("Kata sandi tidak sama.")
            return
        self.username = username
        self.password = password
        self.accept()
