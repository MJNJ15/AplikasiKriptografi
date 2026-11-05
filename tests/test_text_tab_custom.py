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
    tab = TextTab(lambda: TEXT_KEYS)
    tab.input_edit.setPlainText("pesan dengan kunci kustom")
    tab.key_edit.setText(CUSTOM_KEY)
    tab.encrypt_btn.click()
    blob = tab.output_edit.toPlainText()
    assert blob
    tab.decrypt_btn.click()
    assert tab.input_edit.toPlainText() == "pesan dengan kunci kustom"


def test_custom_key_differs_from_session_key(qapp):
    a = TextTab(lambda: TEXT_KEYS)
    a.input_edit.setPlainText("pesan yang sama")
    a.encrypt_btn.click()
    blob_session = a.output_edit.toPlainText()

    b = TextTab(lambda: TEXT_KEYS)
    b.input_edit.setPlainText("pesan yang sama")
    b.key_edit.setText(CUSTOM_KEY)
    b.encrypt_btn.click()
    blob_custom = b.output_edit.toPlainText()

    assert blob_session != blob_custom
    # blob kustom bisa didekripsi dengan kunci kustom yang sama
    custom_keys = b._keys()
    assert decrypt_text(blob_custom, *custom_keys) == "pesan yang sama"


def test_empty_custom_uses_session_keys(qapp):
    tab = TextTab(lambda: TEXT_KEYS)
    assert tab.key_edit.text() == ""
    tab.input_edit.setPlainText("pesan sesi")
    tab.encrypt_btn.click()
    blob = tab.output_edit.toPlainText()
    assert decrypt_text(blob, *TEXT_KEYS) == "pesan sesi"
