"""Dialog login: kata sandi + opsi biometrik wajah.

Dialog tidak melakukan verifikasi sendiri — menerima callback:
  - `verify(username, password) -> (ok, pesan)`  (kata sandi)
  - `face_verify(username) -> (ok, pesan)`        (wajah)
Bila verifikasi sukses, dialog `accept()`; hasil tersimpan di atribut
`username` dan `session` (diisi callback). 
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


from .main_window import WINDOW_HEIGHT, WINDOW_WIDTH


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

        self.username_edit = QLineEdit(initial_username)
        self.username_edit.setPlaceholderText("Username")
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Kata sandi")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_btn = QPushButton("Login")
        self.face_btn = QPushButton("Login Wajah")
        self.face_btn.setVisible(face_verify is not None)
        self.status_label = QLabel("Silakan masuk.")

        self.login_btn.clicked.connect(self._on_login)
        self.face_btn.clicked.connect(self._on_face)
        self.password_edit.returnPressed.connect(self._on_login)

        form = QFormLayout()
        form.addRow("Username:", self.username_edit)
        form.addRow("Kata sandi:", self.password_edit)

        buttons = QHBoxLayout()
        buttons.addWidget(self.login_btn)
        buttons.addWidget(self.face_btn)
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(self.status_label)

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
