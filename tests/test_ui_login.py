"""Uji dialog login (offscreen)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.ui.login_dialog import LoginDialog


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_login_success_accepts(qapp):
    dlg = LoginDialog(verify=lambda u, p: (True, ""), initial_username="budi")
    dlg.username_edit.setText("budi")
    dlg.password_edit.setText("pw")
    dlg.login_btn.click()
    assert dlg.result() == LoginDialog.DialogCode.Accepted
    assert dlg.username == "budi"


def test_login_failure_does_not_accept(qapp, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    dlg = LoginDialog(verify=lambda u, p: (False, "username/kata sandi salah"))
    dlg.username_edit.setText("budi")
    dlg.password_edit.setText("salah")
    dlg.login_btn.click()
    assert dlg.result() != LoginDialog.DialogCode.Accepted
    assert "salah" in dlg.status_label.text()


def test_login_with_face_callback_requires_face(qapp, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    dlg = LoginDialog(
        verify=lambda u, p: (True, ""),
        face_verify=lambda u: (False, "verifikasi wajah dibatalkan/gagal"),
    )
    dlg.username_edit.setText("budi")
    dlg.password_edit.setText("pw")
    dlg.login_btn.click()
    assert dlg.result() != LoginDialog.DialogCode.Accepted
    assert "wajah" in dlg.status_label.text().lower()


def test_login_single_flow_with_face_success(qapp):
    dlg = LoginDialog(
        verify=lambda u, p: (True, ""),
        face_verify=lambda u: (True, ""),
    )
    dlg.username_edit.setText("budi")
    dlg.password_edit.setText("pw")
    dlg.login_btn.click()
    assert dlg.result() == LoginDialog.DialogCode.Accepted
    assert dlg.username == "budi"


def test_login_without_face_callback_skips_face(qapp):
    dlg = LoginDialog(verify=lambda u, p: (True, ""))
    dlg.username_edit.setText("budi")
    dlg.password_edit.setText("pw")
    dlg.login_btn.click()
    assert dlg.result() == LoginDialog.DialogCode.Accepted
