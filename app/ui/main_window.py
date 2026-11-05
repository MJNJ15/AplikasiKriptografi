"""Jendela utama aplikasi (PySide6) — tab fitur.

Menerima sesi login (app_key) + komponen basis data. Dipakai setelah boot
dongle & login sukses (fase boot/UI akhir).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

from ..core.keys import make_text_keys, derive_subkey
from ..db.database import Database, MessageStore, UserStore
from .db_tab import DbTab
from .file_tab import FileTab
from .text_tab import TextTab


class MainWindow(QMainWindow):
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

        classic_key, des_key, mac_key = make_text_keys(app_key)
        chacha_key = derive_subkey(app_key, "chacha")
        column_key = derive_subkey(app_key, "db")

        text_tab = TextTab(lambda: (classic_key, des_key, mac_key))
        file_tab = FileTab(chacha_key)
        msg_store = MessageStore(db, column_key)
        db_tab = DbTab(msg_store, user_id)

        tabs = QTabWidget()
        tabs.addTab(text_tab, "Teks")
        tabs.addTab(file_tab, "File")
        tabs.addTab(db_tab, "Basis Data")
        self.setCentralWidget(tabs)
        self.resize(760, 560)
