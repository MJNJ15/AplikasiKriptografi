"""Uji inti biometrik (DNN YUNet+SFace) — bagian murni tanpa kamera."""

from __future__ import annotations

import numpy as np
import pytest

from app.security.biometric import FaceBiometrics

EMB_A = np.array([1.0, 0.0, 0.0], dtype=np.float32)
EMB_B = np.array([0.0, 1.0, 0.0], dtype=np.float32)
EMB_C = np.array([0.9, 0.1, 0.0], dtype=np.float32)


def test_cosine_basic():
    assert FaceBiometrics.cosine(EMB_A, EMB_A) == pytest.approx(1.0)
    assert FaceBiometrics.cosine(EMB_A, EMB_B) == pytest.approx(0.0)


def test_similarity_percent_after_enroll():
    bio = FaceBiometrics()
    bio._template_emb = EMB_A
    bio._template_count = 1
    assert bio.similarity_percent(EMB_A) == pytest.approx(100.0)
    assert bio.similarity_percent(EMB_B) == pytest.approx(0.0)
    sim_c = bio.similarity_percent(EMB_C)
    assert 85.0 < sim_c < 100.0


def test_save_load_template_roundtrip():
    bio = FaceBiometrics()
    bio._template_emb = EMB_C
    bio._template_count = 5
    blob = bio.save_template()

    bio2 = FaceBiometrics()
    bio2.load_template(blob)
    assert bio2.has_template()
    assert bio2._template_count == 5
    assert np.allclose(bio2._template_emb, EMB_C)


def test_load_invalid_template_rejected():
    bio = FaceBiometrics()
    with pytest.raises(Exception):
        bio.load_template(b"\x00\x01\x02")


def test_draw_detection_boxes():
    frame = np.zeros((120, 120, 3), dtype=np.uint8)
    out = FaceBiometrics.draw_detection(frame, [(10, 10, 40, 40)], "99%")
    assert out.shape == frame.shape
    # kotak membentuk perubahan piksel di area garis
    assert out[10, 10].sum() > 0


def test_detect_faces_accepts_any_frame_size():
    """Regresi: YUNet harus menerima ukuran frame non-320x320."""
    bio = FaceBiometrics()
    for size in ((640, 480), (320, 240), (1280, 720)):
        frame = np.random.default_rng(3).integers(0, 256, (*size, 3), dtype=np.uint8)
        boxes = bio.detect_faces(frame)
        assert isinstance(boxes, list)


def test_normalize_lighting_shape():
    bio = FaceBiometrics()
    crop = np.random.default_rng(0).integers(0, 256, (112, 112, 3), dtype=np.uint8)
    out = bio.normalize_lighting(crop)
    assert out.shape == crop.shape
    assert out.dtype == np.uint8
