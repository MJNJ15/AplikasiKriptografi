"""Uji TextTab: kolom kunci per-algoritma."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.core.super_encrypt import decrypt_text
from app.ui.text_tab import TextTab


def _fill_keys(tab: TextTab) -> None:
    tab.vigenere_edit.setText("LEMON")
    tab.caesar_edit.setText("C")
    tab.lfsr_edit.setText("SEED1234")
    tab.des_edit.setText("DESKEY8!")
    tab.mac_edit.setText("MAC-KUNCI-12345678")


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_five_key_columns_exist(qapp):
    tab = TextTab()
    for attr in ("vigenere_edit", "caesar_edit", "lfsr_edit", "des_edit", "mac_edit"):
        assert hasattr(tab, attr), attr


def test_roundtrip_with_all_keys(qapp):
    tab = TextTab()
    _fill_keys(tab)
    tab.input_edit.setPlainText("pesan dengan kunci per algoritma")
    tab.encrypt_btn.click()
    blob = tab.output_edit.toPlainText()
    assert blob
    tab.decrypt_btn.click()
    assert tab.input_edit.toPlainText() == "pesan dengan kunci per algoritma"


def test_changing_one_key_changes_ciphertext(qapp):
    a = TextTab()
    _fill_keys(a)
    a.input_edit.setPlainText("pesan yang sama")
    a.encrypt_btn.click()
    blob_a = a.output_edit.toPlainText()

    b = TextTab()
    _fill_keys(b)
    b.mac_edit.setText("MAC-YANG-LAIN-1111")
    b.input_edit.setPlainText("pesan yang sama")
    b.encrypt_btn.click()
    blob_b = b.output_edit.toPlainText()

    assert blob_a != blob_b
    keys_b = b._parse_keys()
    assert keys_b is not None
    assert decrypt_text(blob_b, keys_b) == "pesan yang sama"


def test_missing_any_key_blocked(qapp):
    tab = TextTab()
    _fill_keys(tab)
    tab.vigenere_edit.clear()
    tab.input_edit.setPlainText("pesan")
    tab.encrypt_btn.click()
    assert tab.output_edit.toPlainText() == ""
    assert "wajib" in tab.status_label.text().lower()


def test_lfsr_short_key_blocked(qapp):
    tab = TextTab()
    _fill_keys(tab)
    tab.lfsr_edit.setText("abc")
    tab.input_edit.setPlainText("pesan")
    tab.encrypt_btn.click()
    assert tab.output_edit.toPlainText() == ""
    assert "lfsr" in tab.status_label.text().lower()
