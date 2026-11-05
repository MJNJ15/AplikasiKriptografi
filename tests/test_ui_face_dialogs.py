"""Uji dialog webcam biometrik (offscreen + kamera tiruan)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import cv2
import numpy as np
import pytest

from PySide6.QtWidgets import QDialog

from app.security.biometric import FaceBiometrics
from app.ui.face_dialogs import (
    NEEDED_FRAMES,
    EnrollFaceDialog,
    VerifyFaceDialog,
)


def _pattern(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 256, (200, 200), dtype=np.uint8)
    return cv2.GaussianBlur(base, (15, 15), 0)


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


def _force_extract(dlg):
    """Tanpa Haar (foto sintetis tidak terdeteksi), ekstrak langsung."""
    dlg._bio.extract_face = (
        lambda f: FaceBiometrics.normalize_face(FaceBiometrics.to_gray(f))
    )


def test_enroll_dialog_auto_capture(qapp):
    dlg = EnrollFaceDialog(capture_factory=lambda i: FakeCapture(_pattern(1)))
    _force_extract(dlg)
    for _ in range(NEEDED_FRAMES):
        dlg._on_frame(_pattern(1))
    assert dlg.result() == QDialog.DialogCode.Accepted
    assert dlg.template_bytes is not None
    # template dapat dimuat ulang untuk verifikasi
    bio = FaceBiometrics()
    bio.load_template(dlg.template_bytes)
    assert bio.is_match(_pattern(1)) is True


def test_enroll_timeout_rejects(qapp):
    import time as _time

    dlg = EnrollFaceDialog(capture_factory=lambda i: FakeCapture(_pattern(1)))
    _force_extract(dlg)
    dlg._deadline = _time.monotonic() - 1
    dlg._on_frame(_pattern(1))
    assert dlg.result() != QDialog.DialogCode.Accepted
    assert dlg.template_bytes is None


def test_verify_dialog_accepts_matching(qapp):
    p = _pattern(1)
    bio = FaceBiometrics()
    bio.enroll([p])
    template = bio.save_template()
    dlg = VerifyFaceDialog(template, capture_factory=lambda i: FakeCapture(p))
    dlg._on_frame(p)
    assert dlg.result() == QDialog.DialogCode.Accepted


def test_verify_dialog_rejects_wrong(qapp):
    p1, p2 = _pattern(1), _pattern(2)
    bio = FaceBiometrics()
    bio.enroll([p1])
    template = bio.save_template()
    dlg = VerifyFaceDialog(template, capture_factory=lambda i: FakeCapture(p2))
    # Simulasikan hasil pencocokan gagal (logika LBPH diuji terpisah)
    dlg._bio.is_match = lambda f: False
    dlg._on_frame(p2)
    assert dlg.result() != QDialog.DialogCode.Accepted
