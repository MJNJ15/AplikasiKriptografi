"""Uji template wajah: simpan/muat & enkripsi/dekripsi."""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from cryptography.exceptions import InvalidTag

from app.security.biometric import FaceBiometrics
from app.security.face_login import decrypt_template, encrypt_template

DB_KEY = bytes(range(32))


def _pattern(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 256, (200, 200), dtype=np.uint8)
    return cv2.GaussianBlur(base, (15, 15), 0)


def _shift(img, dx, dy):
    m = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, m, (img.shape[1], img.shape[0]))


def test_template_save_load_roundtrip():
    bio = FaceBiometrics()
    person = _pattern(1)
    bio.enroll([person, _shift(person, 2, 0)])
    blob = bio.save_template()

    bio2 = FaceBiometrics()
    bio2.load_template(blob)
    assert bio2.is_match(person) is True


def test_template_encrypt_decrypt():
    bio = FaceBiometrics()
    person = _pattern(2)
    bio.enroll([person])
    template = bio.save_template()
    blob = encrypt_template(DB_KEY, template)
    assert blob != template
    assert decrypt_template(DB_KEY, blob) == template


def test_template_wrong_key_fails():
    template = b"S" * 128
    blob = encrypt_template(DB_KEY, template)
    with pytest.raises(InvalidTag):
        decrypt_template(b"X" * 32, blob)
