"""Uji dialog wajah (offscreen + kamera tiruan + model DNN)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

from PySide6.QtWidgets import QDialog

from app.security.biometric import FaceBiometrics
from app.ui.face_dialogs import (
    VERIFY_CONSECUTIVE,
    CaptureFaceDialog,
    VerifyFaceDialog,
)


class FakeCapture:
    def __init__(self, frame=None, opened=True):
        self._frame = frame
        self._opened = opened

    def isOpened(self):
        return self._opened

    def read(self):
        return True, self._frame

    def release(self):
        pass


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def _frame():
    return np.random.default_rng(7).integers(0, 256, (200, 200, 3), dtype=np.uint8)


def test_capture_dialog_saves_template(qapp):
    dlg = CaptureFaceDialog(capture_factory=lambda i: FakeCapture(_frame()))
    # stub deteksi→embedding agar tanpa wajah asli tetap enroll
    fake_emb = np.full(128, 0.1, dtype=np.float32)
    dlg._bio.extract_embedding = lambda f: fake_emb
    dlg._bio.detect_faces = lambda f: [(10, 10, 80, 80)]
    dlg._on_save()
    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.template_bytes is not None


def test_capture_dialog_no_face_stays_open(qapp):
    dlg = CaptureFaceDialog(capture_factory=lambda i: FakeCapture(_frame()))
    dlg._bio.extract_embedding = lambda f: None
    dlg._on_save()
    assert dlg.result() != QDialog.DialogCode.Accepted
    assert dlg.template_bytes is None


def _make_verify_dialog(percent_fn):
    bio = FaceBiometrics()
    fake_emb = np.full(128, 0.1, dtype=np.float32)
    bio._template_emb = fake_emb
    bio._template_count = 1
    template = bio.save_template()
    dlg = VerifyFaceDialog(template, capture_factory=lambda i: FakeCapture(_frame()))
    dlg._bio.match = percent_fn
    return dlg


def test_verify_dialog_accepts_high_similarity(qapp):
    dlg = _make_verify_dialog(lambda f: (True, True, 95.0, None))
    for _ in range(VERIFY_CONSECUTIVE):
        dlg._on_frame(_frame())
    assert dlg.result() == QDialog.DialogCode.Accepted


def test_verify_dialog_rejects_low_similarity(qapp):
    dlg = _make_verify_dialog(lambda f: (False, True, 20.0, None))
    for _ in range(VERIFY_CONSECUTIVE):
        dlg._on_frame(_frame())
    assert dlg.result() != QDialog.DialogCode.Accepted


def test_verify_dialog_reports_no_face(qapp):
    dlg = _make_verify_dialog(lambda f: (False, False, 0.0, None))
    dlg._on_frame(_frame())
    assert "Tidak ada wajah" in dlg._camera.status_label.text()
