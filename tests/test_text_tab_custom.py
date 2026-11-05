"""Uji TextTab dengan kunci kustom (dan fallback ke kunci sesi)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.core.keys import make_text_keys
from app.core.super_encrypt import decrypt_text
from app.ui.text_tab import TextTab

APP_KEY = bytes(range(32))
TEXT_KEYS = make_text_keys(APP_KEY)
CUSTOM_KEY = "kunci-rahasia-sendiri-123"


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_custom_key_roundtrip(qapp):
    tab = TextTab()
    tab.input_edit.setPlainText("pesan dengan kunci kustom")
    tab.key_edit.setText(CUSTOM_KEY)
    tab.encrypt_btn.click()
    blob = tab.output_edit.toPlainText()
    assert blob
    tab.decrypt_btn.click()
    assert tab.input_edit.toPlainText() == "pesan dengan kunci kustom"


def test_custom_key_differs_from_other_key(qapp):
    a = TextTab()
    a.input_edit.setPlainText("pesan yang sama")
    a.key_edit.setText(CUSTOM_KEY)
    a.encrypt_btn.click()
    blob_a = a.output_edit.toPlainText()

    b = TextTab()
    b.input_edit.setPlainText("pesan yang sama")
    b.key_edit.setText("kunci-lain-berbeda-999")
    b.encrypt_btn.click()
    blob_b = b.output_edit.toPlainText()

    assert blob_a != blob_b
    keys_a = a._custom_keys()
    keys_b = b._custom_keys()
    assert keys_a is not None and keys_b is not None
    assert decrypt_text(blob_a, *keys_a) == "pesan yang sama"
    assert decrypt_text(blob_b, *keys_b) == "pesan yang sama"


def test_missing_key_is_blocked(qapp):
    tab = TextTab()
    tab.input_edit.setPlainText("pesan tanpa kunci")
    tab.encrypt_btn.click()
    assert tab.output_edit.toPlainText() == ""
    assert "wajib" in tab.status_label.text().lower()


def test_keys_distinct_per_algorithm():
    from app.core.keys import keys_from_custom

    classic, des, mac = keys_from_custom(CUSTOM_KEY.encode("utf-8"))
    assert len({classic, des, mac}) == 3
    assert classic != des != mac
