"""Uji TextTab: kolom kunci per-algoritma."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.core.super_encrypt import decrypt_text
from app.ui.text_tab import TextTab


def _fill_keys(panel) -> None:
    panel.vigenere_edit.setText("LEMON")
    panel.caesar_edit.setText("C")
    panel.des_edit.setText("DESKEY8!")
    panel.aes_edit.setText("AES-RIJNDAEL-2025")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_two_subtabs_exist(qapp):
    tab = TextTab()
    assert hasattr(tab, "encrypt_panel")
    assert hasattr(tab, "decrypt_panel")
    assert tab.encrypt_panel.mode == "encrypt"
    assert tab.decrypt_panel.mode == "decrypt"


def test_four_key_columns_exist(qapp):
    tab = TextTab()
    for attr in ("vigenere_edit", "caesar_edit", "des_edit", "aes_edit"):
        assert hasattr(tab.encrypt_panel, attr), attr
        assert hasattr(tab.decrypt_panel, attr), attr


def test_roundtrip_with_all_keys(qapp):
    tab = TextTab()
    p = tab.encrypt_panel
    _fill_keys(p)
    p.input_edit.setPlainText("pesan dengan kunci per algoritma")
    p.action_btn.click()
    blob = p.output_edit.toPlainText()
    assert blob

    d = tab.decrypt_panel
    _fill_keys(d)
    d.input_edit.setPlainText(blob)
    d.action_btn.click()
    assert d.output_edit.toPlainText() == "pesan dengan kunci per algoritma"


def test_changing_one_key_changes_ciphertext(qapp):
    a = TextTab()
    _fill_keys(a.encrypt_panel)
    a.encrypt_panel.input_edit.setPlainText("pesan yang sama")
    a.encrypt_panel.action_btn.click()
    blob_a = a.encrypt_panel.output_edit.toPlainText()

    b = TextTab()
    _fill_keys(b.encrypt_panel)
    b.encrypt_panel.aes_edit.setText("AES-YANG-LAIN-2026-BERBEDA")
    b.encrypt_panel.input_edit.setPlainText("pesan yang sama")
    b.encrypt_panel.action_btn.click()
    blob_b = b.encrypt_panel.output_edit.toPlainText()

    assert blob_a != blob_b
    keys_b = b.encrypt_panel._parse_keys()
    assert keys_b is not None
    assert decrypt_text(blob_b, keys_b) == "pesan yang sama"


def test_missing_any_key_blocked(qapp):
    tab = TextTab()
    p = tab.encrypt_panel
    _fill_keys(p)
    p.vigenere_edit.clear()
    p.input_edit.setPlainText("pesan")
    p.action_btn.click()
    assert p.output_edit.toPlainText() == ""
    assert "wajib" in p.status_label.text().lower()


def test_clear_input_button_only_clears_input(qapp):
    tab = TextTab()
    p = tab.encrypt_panel
    _fill_keys(p)
    p.input_edit.setPlainText("pesan asli")
    p.output_edit.setPlainText("HASIL-LAMA")
    p.reset_btn.click()
    assert p.input_edit.toPlainText() == ""
    assert p.output_edit.toPlainText() == "HASIL-LAMA"
    assert p.vigenere_edit.text() == "LEMON"
    assert "dibersihkan" in p.status_label.text().lower()
