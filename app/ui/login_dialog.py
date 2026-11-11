"""Dialog login tunggal: username + kata sandi + wajah (dua/tiga faktor).

Dialog tidak melakukan verifikasi sendiri — menerima callback:
  - `verify(username, password) -> (ok, pesan)`   (kata sandi)
  - `face_verify(username) -> (ok, pesan)`        (wajah; optional)
  - `register_handler() -> None`                  (buka dialog daftar akun)
Bila `face_verify` diberikan, setelah kata sandi cocok verifikasi wajah
dijalankan otomatis dalam alur login yang sama (tombol login tunggal).
Bila semua lolos, dialog `accept()`; hasil tersimpan di atribut `username`
dan `session` (diisi callback).

Tampilan: split-screen — hero gambar Unsplash (kiri) + kartu login (kanan)
dengan bayangan halus dan animasi fade-in saat dibuka.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .animations import fade_in
from .main_window import WINDOW_HEIGHT, WINDOW_WIDTH
from .theme import make_theme_toggle_button

CARD_WIDTH = 460
HERO_MIN_WIDTH = 400

_ASSETS = Path(__file__).resolve().parent / "assets"
HERO_IMAGE = _ASSETS / "login_hero.jpg"


def _cover_pixmap(path: Path, width: int, height: int) -> QPixmap:
    """Skala potong-tutup (cover) supaya gambar mengisi label tanpa distorsi."""
    pm = QPixmap(str(path))
    if pm.isNull() or width <= 0 or height <= 0:
        return QPixmap()
    scaled = pm.scaled(
        width,
        height,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = (scaled.width() - width) // 2
    y = (scaled.height() - height) // 2
    return scaled.copy(x, y, width, height)


class LoginDialog(QDialog):
    def __init__(
        self,
        verify: Callable[[str, str], tuple[bool, str]],
        face_verify: Optional[Callable[[str], tuple[bool, str]]] = None,
        initial_username: str = "",
        register_handler: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Login — Aplikasi Kriptografi")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self._verify = verify
        self._face_verify = face_verify
        self._register_handler = register_handler
        self.username: str = ""
        self.session = None

        # --- hero kiri: gambar Unsplash + scrim + teks motif ---
        hero = QFrame()
        hero.setObjectName("heroPanel")
        hero.setMinimumWidth(HERO_MIN_WIDTH)

        self._hero_image = QLabel()
        self._hero_image.setObjectName("heroImage")

        scrim = QLabel()
        scrim.setObjectName("loginScrim")

        hero_title = QLabel("Amankan Data Anda")
        hero_title.setObjectName("heroTitle")
        hero_subtitle = QLabel("Enkripsi  •  Biometrik  •  Dongle")
        hero_subtitle.setObjectName("heroSubtitle")
        hero_tag = QLabel("Kriptografi modern untuk data pribadi Anda")
        hero_tag.setObjectName("heroTag")
        footer_note = QLabel("© 2026 • Projek Akhir Kriptografi")
        footer_note.setObjectName("heroTag")

        text_col = QVBoxLayout()
        text_col.setContentsMargins(36, 28, 36, 32)
        text_col.setSpacing(8)
        text_col.addStretch(1)
        text_col.addWidget(hero_title)
        text_col.addWidget(hero_subtitle)
        text_col.addWidget(hero_tag)
        text_col.addStretch(3)
        text_col.addWidget(footer_note)

        text_wrap = QWidget()
        text_wrap.setLayout(text_col)

        hero_grid = QGridLayout(hero)
        hero_grid.setContentsMargins(0, 0, 0, 0)
        hero_grid.setSpacing(0)
        hero_grid.addWidget(self._hero_image, 0, 0)
        hero_grid.addWidget(scrim, 0, 0)
        hero_grid.addWidget(
            text_wrap,
            0,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
        )

        # --- kartu kanan ---
        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(CARD_WIDTH)

        title = QLabel("Aplikasi Kriptografi")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Masuk untuk membuka aplikasi")
        subtitle.setObjectName("subtitleLabel")

        # Username sengaja selalu kosong saat login (tidak memakai
        # initial_username) — parameter dipertahankan untuk kompatibilitas API.
        self.username_edit = QLineEdit()
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

        self.register_btn = QPushButton("Buat Akun Baru")
        self.register_btn.setObjectName("secondaryBtn")
        self.register_btn.setVisible(register_handler is not None)

        self.status_label = QLabel("Silakan masuk.")
        self.status_label.setObjectName("statusLabel")

        self.login_btn.clicked.connect(self._on_login)
        self.register_btn.clicked.connect(self._on_register)
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
        card_layout.addWidget(self.register_btn)
        card_layout.addSpacing(6)
        card_layout.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignHCenter)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(9, 12, 26, 90))
        card.setGraphicsEffect(shadow)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24, 24, 24, 16)
        right_layout.addStretch(1)
        right_layout.addWidget(card, 0, Qt.AlignmentFlag.AlignHCenter)
        right_layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(make_theme_toggle_button())
        right_layout.addLayout(footer)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(hero)
        outer.addWidget(right, 1)

        self._refresh_hero()

    def _refresh_hero(self) -> None:
        size = self._hero_image.size()
        if size.isValid() and size.width() > 0 and size.height() > 0:
            pm = _cover_pixmap(HERO_IMAGE, size.width(), size.height())
            if not pm.isNull():
                self._hero_image.setPixmap(pm)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        fade_in(self)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_hero()

    def _on_register(self) -> None:
        if self._register_handler is not None:
            self._register_handler()

    def _on_login(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self.status_label.setText("Username dan kata sandi wajib diisi.")
            return
        ok, msg = self._verify(username, password)
        if not ok:
            self.status_label.setText(msg)
            QMessageBox.warning(self, "Login", msg)
            return
        if self._face_verify is not None:
            ok, msg = self._face_verify(username)
            if not ok:
                self.status_label.setText(msg)
                QMessageBox.warning(self, "Login", msg)
                return
        self.username = username
        self.accept()
