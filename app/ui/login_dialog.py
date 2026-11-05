"""Dialog login: kata sandi + opsi biometrik wajah.

Dialog tidak melakukan verifikasi sendiri — menerima callback:
  - `verify(username, password) -> (ok, pesan)`  (kata sandi)
  - `face_verify(username) -> (ok, pesan)`        (wajah)
Bila verifikasi sukses, dialog `accept()`; hasil tersimpan di atribut
`username` dan `session` (diisi callback).

Tampilan: card terpusat dengan gaya tema (lihat theme.py).
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .main_window import WINDOW_HEIGHT, WINDOW_WIDTH

CARD_WIDTH = 460


class LoginDialog(QDialog):
    def __init__(
        self,
        verify: Callable[[str, str], tuple[bool, str]],
        face_verify: Optional[Callable[[str], tuple[bool, str]]] = None,
        initial_username: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Login — Aplikasi Kriptografi")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self._verify = verify
        self._face_verify = face_verify
        self.username: str = ""
        self.session = None

        # --- kartu login ---
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(CARD_WIDTH)

        title = QLabel("Aplikasi Kriptografi")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Masuk untuk membuka aplikasi")
        subtitle.setObjectName("subtitleLabel")

        self.username_edit = QLineEdit(initial_username)
        self.username_edit.setObjectName("inputField")
        self.username_edit.setPlaceholderText("contoh: budi")
        self.password_edit = QLineEdit()
        self.password_edit.setObjectName("inputField")
        self.password_edit.setPlaceholderText("••••••••")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        user_label = QLabel("Username")
        user_label.setObjectName("fieldLabel")
        pass_label = QLabel("Kata sandi")
        pass_label.setObjectName("fieldLabel")

        self.login_btn = QPushButton("Login")
        self.login_btn.setObjectName("primaryBtn")
        self.face_btn = QPushButton("Login Wajah")
        self.face_btn.setObjectName("secondaryBtn")
        self.face_btn.setVisible(face_verify is not None)

        self.status_label = QLabel("Silakan masuk.")
        self.status_label.setObjectName("statusLabel")

        self.login_btn.clicked.connect(self._on_login)
        self.face_btn.clicked.connect(self._on_face)
        self.password_edit.returnPressed.connect(self._on_login)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 36, 40, 36)
        card_layout.setSpacing(12)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(16)
        card_layout.addWidget(user_label)
        card_layout.addWidget(self.username_edit)
        card_layout.addSpacing(6)
        card_layout.addWidget(pass_label)
        card_layout.addWidget(self.password_edit)
        card_layout.addSpacing(18)
        card_layout.addWidget(self.login_btn)
        card_layout.addWidget(self.face_btn)
        card_layout.addSpacing(6)
        card_layout.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignHCenter)

        outer = QVBoxLayout(self)
        outer.addStretch(1)
        outer.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addStretch(1)

    def _on_login(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self.status_label.setText("Username dan kata sandi wajib diisi.")
            return
        ok, msg = self._verify(username, password)
        if ok:
            self.username = username
            self.accept()
        else:
            self.status_label.setText(msg)
            QMessageBox.warning(self, "Login", msg)

    def _on_face(self) -> None:
        if self._face_verify is None:
            return
        username = self.username_edit.text().strip()
        if not username:
            self.status_label.setText("Isi username dulu.")
            return
        ok, msg = self._face_verify(username)
        if ok:
            self.username = username
            self.accept()
        else:
            self.status_label.setText(msg)
            QMessageBox.warning(self, "Login Wajah", msg)
