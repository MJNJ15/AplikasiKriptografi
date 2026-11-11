"""Jendela utama aplikasi (PySide6) — tab fitur.

Menerima sesi login (app_key) + komponen basis data. Dipakai setelah boot
dongle & login sukses (fase boot/UI akhir). Header bar di atas tab berisi
brand, chip pengguna, tombol Logout, dan toggle tema.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.keys import derive_subkey
from ..db.database import Database, MessageStore, UserStore
from .animations import fade_in, fade_reveal
from .asset_tab import AssetTab
from .db_tab import DbTab
from .file_tab import FileTab
from .icons import load_pixmap
from .image_tab import ImageTab
from .text_tab import TextTab
from .theme import current_colors, make_theme_toggle_button

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720

TAB_ICONS = ("text", "file", "db", "image", "asset")


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(
        self,
        app_key: bytes,
        store: UserStore,
        db: Database,
        user_id: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Aplikasi Kriptografi")

        chacha_key = derive_subkey(app_key, "chacha")
        column_key = derive_subkey(app_key, "db")

        text_tab = TextTab()
        file_tab = FileTab(chacha_key)
        msg_store = MessageStore(db, column_key)
        db_tab = DbTab(msg_store, user_id)
        image_tab = ImageTab()
        asset_tab = AssetTab()

        tabs = QTabWidget()
        tabs.setIconSize(QSize(18, 18))
        tabs.addTab(text_tab, load_pixmap("text", "#5B6B7A", 18), "Teks")
        tabs.addTab(file_tab, load_pixmap("file", "#5B6B7A", 18), "File")
        tabs.addTab(db_tab, load_pixmap("db", "#5B6B7A", 18), "Basis Data")
        tabs.addTab(image_tab, load_pixmap("image", "#5B6B7A", 18), "Gambar")
        tabs.addTab(asset_tab, load_pixmap("asset", "#5B6B7A", 18), "Aset")
        tabs.currentChanged.connect(self._on_tab_changed)
        self._tabs = tabs
        self._update_tab_icons()

        header = self._build_header(store, user_id)

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(header)
        central_layout.addWidget(tabs, 1)
        self.setCentralWidget(central)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.statusBar().hide()

    def _build_header(self, store: UserStore, user_id: int) -> QFrame:
        username = next(
            (u["username"] for u in store.list_users() if u["id"] == user_id),
            f"user-{user_id}",
        )

        header = QFrame()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 12, 8)
        header_layout.setSpacing(10)

        brand_icon = QLabel()
        brand_icon.setPixmap(load_pixmap("shield", "#FFFFFF", 22))
        brand_title = QLabel("Aplikasi Kriptografi")
        brand_title.setObjectName("brandTitle")
        brand_subtitle = QLabel("Enkripsi  •  Biometrik  •  Dongle")
        brand_subtitle.setObjectName("brandSubtitle")
        brand_col = QVBoxLayout()
        brand_col.setContentsMargins(0, 0, 0, 0)
        brand_col.setSpacing(0)
        brand_col.addWidget(brand_title)
        brand_col.addWidget(brand_subtitle)

        header_layout.addWidget(brand_icon)
        header_layout.addLayout(brand_col)
        header_layout.addStretch(1)

        chip = QFrame()
        chip.setObjectName("userChip")
        chip.setFrameShape(QFrame.Shape.NoFrame)
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(6, 3, 10, 3)
        chip_layout.setSpacing(6)
        user_icon = QLabel()
        user_icon.setPixmap(load_pixmap("user", "#FFFFFF", 16))
        user_label = QLabel(username)
        user_label.setStyleSheet("font-weight: 600;")
        chip_layout.addWidget(user_icon)
        chip_layout.addWidget(user_label)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setToolTip("Keluar dari akun dan kembali ke layar login")
        logout_btn.clicked.connect(self.logout_requested)

        theme_btn = make_theme_toggle_button(self._update_tab_icons)
        for control in (chip, logout_btn, theme_btn):
            control.setFixedHeight(34)

        header_layout.addWidget(chip)
        header_layout.addWidget(logout_btn)
        header_layout.addWidget(theme_btn)
        return header

    def showEvent(self, event) -> None:
        super().showEvent(event)
        fade_in(self)

    def _on_tab_changed(self, index: int) -> None:
        self._update_tab_icons()
        page = self._tabs.widget(index)
        if page is not None and self.isVisible():
            fade_reveal(page)

    def _update_tab_icons(self) -> None:
        colors = current_colors()
        selected = self._tabs.currentIndex()
        for i, name in enumerate(TAB_ICONS):
            color = colors["tab_selected_fg"] if i == selected else colors["text_muted"]
            self._tabs.setTabIcon(i, load_pixmap(name, color, 18))
