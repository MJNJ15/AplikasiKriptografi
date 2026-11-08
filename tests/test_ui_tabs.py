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
    panel.des_edit.setText("DESKEY8!")
    panel.aes_edit.setText("AES-RIJNDAEL-2025")


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
    add_panel, view_panel = tab.add_panel, tab.view_panel
    assert view_panel.table.rowCount() == 0

    # Pesan penting
    add_panel.title_edit.setText("Catatan rahasia")
    add_panel.body_edit.setPlainText("isi penting")
    add_panel.important_check.setChecked(True)
    add_panel.save_btn.click()

    assert view_panel.table.rowCount() == 1
    rows = store.list_messages(1)
    assert rows[0]["judul"] == "Catatan rahasia"
    assert rows[0]["is_penting"] == 1

    # Tampilan default: ciphertext (bukan teks asli)
    view_panel.table.selectRow(0)
    view_panel.view_btn.click()
    assert not view_panel.reveal_btn.isHidden()
    assert view_panel.output_edit.toPlainText() != "isi penting"
    assert view_panel.reveal_btn.text() == "Tampilkan Isi Asli"
    assert "ciphertext" in view_panel.status_label.text()

    # Tombol reveal → teks asli
    view_panel.reveal_btn.click()
    assert view_panel.output_edit.toPlainText() == "isi penting"
    assert view_panel.reveal_btn.text() == "Tampilkan Ciphertext"
    assert "dekripsi" in view_panel.status_label.text()

    # Toggle balik → ciphertext lagi
    view_panel.reveal_btn.click()
    assert view_panel.output_edit.toPlainText() != "isi penting"
    assert view_panel.reveal_btn.text() == "Tampilkan Isi Asli"

    # Pesan tidak penting → teks langsung, tanpa tombol reveal
    add_panel.title_edit.setText("Catatan biasa")
    add_panel.body_edit.setPlainText("isi biasa")
    add_panel.important_check.setChecked(False)
    add_panel.save_btn.click()
    assert view_panel.table.rowCount() == 2
    view_panel.table.selectRow(0)
    view_panel.view_btn.click()
    assert view_panel.reveal_btn.isHidden()
    assert "isi biasa" in view_panel.output_edit.toPlainText()


def test_file_tab_encrypt_decrypt(qapp, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    src = tmp_path / "dokumen.txt"
    src.write_text("PDF rahasia", encoding="utf-8")

    tab = FileTab(CHACHA_KEY)
    ep, dp = tab.encrypt_panel, tab.decrypt_panel

    # Enkripsi
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(src), ""))
    ep.choose_btn.click()
    assert ep._path == src
    assert not ep.text_preview.isHidden()  # preview teks tampil
    assert "PDF rahasia" in ep.text_preview.toPlainText()

    enc = tmp_path / "hasil_enc.enc"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(enc), ""))
    ep.action_btn.click()
    assert enc.exists()
    assert enc.read_bytes() != b"PDF rahasia"

    # Dekripsi
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(enc), ""))
    dp.choose_btn.click()
    assert dp._path == enc
    assert not dp.meta_label.isHidden()
    assert "dikenali" in dp.meta_label.text()
    assert "Nama asli:" in dp.meta_label.text()
    assert "SHA-256" in dp.meta_label.text()
    assert "siap didekripsi" in dp.status_label.text()

    out = tmp_path / "hasil_dec.txt"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(out), ""))
    dp.action_btn.click()
    assert out.read_text(encoding="utf-8") == "PDF rahasia"
