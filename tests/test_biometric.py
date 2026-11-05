"""Uji biometrik wajah (LBPH + liveness ringan)."""

from __future__ import annotations

import cv2
import numpy as np

from app.security.biometric import DEFAULT_MATCH_THRESHOLD, FaceBiometrics


def _pattern(seed: int) -> np.ndarray:
    """Wajah sintetis bertekstur: blur Gaussian dari noise halus ber-seed."""
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 256, (200, 200), dtype=np.uint8)
    return cv2.GaussianBlur(base, (15, 15), 0)


def _shift(img: np.ndarray, dx: int, dy: int) -> np.ndarray:
    m = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, m, (img.shape[1], img.shape[0]))


def test_enroll_and_match_self():
    bio = FaceBiometrics(threshold=DEFAULT_MATCH_THRESHOLD)
    person_a = _pattern(1)
    bio.enroll([person_a, _shift(person_a, 2, 0), _shift(person_a, -2, 1)])
    assert bio.is_match(person_a) is True


def test_match_rejects_different_pattern():
    bio = FaceBiometrics()
    person_a = _pattern(1)
    person_b = _pattern(2)
    bio.enroll([person_a, _shift(person_a, 2, 0)])
    _, conf_a = bio.predict(person_a)
    _, conf_b = bio.predict(person_b)
    assert conf_a < conf_b
    # threshold di tengah-tengah — robust terhadap skala confidence LBPH
    mid = (conf_a + conf_b) / 2.0
    bio.threshold = mid
    assert bio.is_match(person_a) is True
    assert bio.is_match(person_b) is False


def test_predict_before_enroll_raises():
    bio = FaceBiometrics()
    with np.testing.assert_raises(RuntimeError):
        bio.predict(_pattern(1))


def test_enroll_empty_rejected():
    bio = FaceBiometrics()
    try:
        bio.enroll([])
    except ValueError:
        pass
    else:
        raise AssertionError("enroll kosong harus error")


class FakeEyeCascade:
    """Mata 'terbuka' bila frame terang, 'tertutup' bila gelap."""

    def detectMultiScale(self, gray, **kwargs):
        if float(np.mean(gray)) < 50:
            return []
        return [[0, 0, 30, 30], [40, 0, 30, 30]]


def test_blink_detected_heuristic():
    bio = FaceBiometrics()
    bio._eye_cascade = FakeEyeCascade()
    bright = np.full((200, 200), 180, dtype=np.uint8)
    dark = np.full((200, 200), 10, dtype=np.uint8)
    assert bio.blink_detected([bright, dark]) is True
    assert bio.blink_detected([bright, bright]) is False
    assert bio.blink_detected([dark, dark]) is False
