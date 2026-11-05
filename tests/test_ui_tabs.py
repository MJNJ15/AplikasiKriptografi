"""Uji UI offscreen: TextTab, FileTab, DbTab (PySide6, QT_QPA_PLATFORM=offscreen)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.core.keys import derive_subkey, make_text_keys
from app.core.super_encrypt import decrypt_text
from app.db.database import Database, MessageStore
from app.ui.db_tab import DbTab
from app.ui.file_tab import FileTab
from app.ui.text_tab import TextTab

APP_KEY = bytes(range(32))
TEXT_KEYS = make_text_keys(APP_KEY)
CHACHA_KEY = derive_subkey(APP_KEY, "chacha")
COLUMN_KEY = derive_subkey(APP_KEY, "db")
DB_KEY = b"K" * 32


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _fill(panel) -> None:
    panel.vigenere_edit.setText("LEMON")
    panel.caesar_edit.setText("C")
    panel.lfsr_edit.setText("SEED1234")
    panel.des_edit.setText("DESKEY8!")
    panel.mac_edit.setText("MAC-KUNCI-12345678")


def test_text_tab_encrypt_decrypt(qapp):
    tab = TextTab()
    p = tab.encrypt_panel
    _fill(p)
    p.input_edit.setPlainText("Halo dunia rahasia 123!")
    p.action_btn.click()
    blob = p.output_edit.toPlainText()
    assert blob

    d = tab.decrypt_panel
    _fill(d)
    d.input_edit.setPlainText(blob)
    d.action_btn.click()
    assert d.output_edit.toPlainText() == "Halo dunia rahasia 123!"


def test_db_tab_save_and_view(qapp, tmp_path):
    db = Database(str(tmp_path / "ui.db"), DB_KEY)
    store = MessageStore(db, COLUMN_KEY)
    tab = DbTab(store, owner_id=1)
    assert tab.table.rowCount() == 0

    tab.title_edit.setText("Catatan rahasia")
    tab.body_edit.setPlainText("isi penting")
    tab.important_check.setChecked(True)
    tab.save_btn.click()

    assert tab.table.rowCount() == 1
    rows = store.list_messages(1)
    assert rows[0]["judul"] == "Catatan rahasia"
    assert rows[0]["is_penting"] == 1

    tab.table.selectRow(0)
    tab.view_btn.click()
    assert tab.body_edit.toPlainText() == "isi penting"


def test_file_tab_encrypt_decrypt(qapp, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    src = tmp_path / "dokumen.txt"
    src.write_text("PDF rahasia", encoding="utf-8")

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(src), ""))
    tab = FileTab(CHACHA_KEY)
    tab.open_btn.click()
    tab.encrypt_btn.click()

    enc = tmp_path / "dokumen.txt.enc"
    assert enc.exists()
    assert enc.read_bytes() != b"PDF rahasia"

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(enc), ""))
    tab.decrypt_btn.click()
    assert src.read_text(encoding="utf-8") == "PDF rahasia"
