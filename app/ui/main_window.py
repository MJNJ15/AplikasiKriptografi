"""Jendela utama aplikasi (PySide6) — tab fitur.

Menerima sesi login (app_key) + komponen basis data. Dipakai setelah boot
dongle & login sukses (fase boot/UI akhir).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMainWindow, QPushButton, QTabWidget, QWidget

from ..core.keys import derive_subkey
from ..db.database import Database, MessageStore, UserStore
from .asset_tab import AssetTab
from .db_tab import DbTab
from .file_tab import FileTab
from .image_tab import ImageTab
from .text_tab import TextTab
from .theme import make_theme_toggle_button

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720


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
        tabs.addTab(text_tab, "Teks")
        tabs.addTab(file_tab, "File")
        tabs.addTab(db_tab, "Basis Data")
        tabs.addTab(image_tab, "Gambar")
        tabs.addTab(asset_tab, "Aset")
        self.setCentralWidget(tabs)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("secondaryBtn")
        logout_btn.setToolTip("Keluar dari akun dan kembali ke layar login")
        logout_btn.clicked.connect(self.logout_requested)
        self.statusBar().addPermanentWidget(logout_btn)
        self.statusBar().addPermanentWidget(make_theme_toggle_button())
