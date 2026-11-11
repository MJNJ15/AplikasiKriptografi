"""Uji dialog pendaftaran akun (GUI, offscreen)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.ui.register_dialog import RegisterDialog


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_register_success_accepts(qapp):
    dlg = RegisterDialog()
    dlg.username_edit.setText("budi")
    dlg.password_edit.setText("rahasia123")
    dlg.confirm_edit.setText("rahasia123")
    dlg.register_btn.click()
    assert dlg.result() == RegisterDialog.DialogCode.Accepted
    assert dlg.username == "budi"
    assert dlg.password == "rahasia123"


def test_register_empty_username_rejected(qapp):
    dlg = RegisterDialog()
    dlg.password_edit.setText("rahasia123")
    dlg.confirm_edit.setText("rahasia123")
    dlg.register_btn.click()
    assert dlg.result() != RegisterDialog.DialogCode.Accepted
    assert "username" in dlg.status_label.text().lower()


def test_register_password_mismatch_rejected(qapp):
    dlg = RegisterDialog()
    dlg.username_edit.setText("budi")
    dlg.password_edit.setText("rahasia123")
    dlg.confirm_edit.setText("beda123")
    dlg.register_btn.click()
    assert dlg.result() != RegisterDialog.DialogCode.Accepted
    assert "tidak sama" in dlg.status_label.text().lower()


def test_register_password_short_rejected(qapp):
    dlg = RegisterDialog()
    dlg.username_edit.setText("budi")
    dlg.password_edit.setText("abc")
    dlg.confirm_edit.setText("abc")
    dlg.register_btn.click()
    assert dlg.result() != RegisterDialog.DialogCode.Accepted
    assert "minimal" in dlg.status_label.text().lower()
