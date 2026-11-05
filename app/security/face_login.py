"""Login biometrik wajah: kaum template terenkripsi di DB, ambil frame live.

Template yang disimpan saat setup berupa sampel wajah normalisasi yang
dienkripsi AES-GCM (kunci = kunci DB dari dongle). Saat login, template
didekripsi → LBPH dilatih ulang → dicocokkan dengan frame webcam.
"""

from __future__ import annotations

import os
from typing import Optional

import cv2

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..db.database import UserStore
from .biometric import FaceBiometrics

NONCE_LEN = 12
MAX_FRAMES = 3


def _encrypt_template(db_key: bytes, template: bytes) -> bytes:
    nonce = os.urandom(NONCE_LEN)
    return nonce + AESGCM(db_key).encrypt(nonce, template, None)


def encrypt_template(db_key: bytes, template: bytes) -> bytes:
    return _encrypt_template(db_key, template)


def decrypt_template(db_key: bytes, blob: bytes) -> bytes:
    if len(blob) < NONCE_LEN + 16:
        raise ValueError("template terenkripsi tidak valid")
    nonce, ct = blob[:NONCE_LEN], blob[NONCE_LEN:]
    return AESGCM(db_key).decrypt(nonce, ct, None)


def capture_and_enroll(camera_index: int = 0, frames: int = MAX_FRAMES) -> Optional[bytes]:
    """Ambil beberapa frame dari webcam, enrol, kembalikan template mentah.

    Mengembalikan None bila kamera tidak tersedia / wajah tidak terdeteksi.
    """
    bio = FaceBiometrics()
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None
    collected = []
    for _ in range(frames):
        ok, frame = cap.read()
        if ok:
            collected.append(frame)
    cap.release()
    if not collected:
        return None
    try:
        bio.enroll(collected)
    except ValueError:
        return None
    return bio.save_template()


def try_face_login(
    store: UserStore,
    username: str,
    db_key: bytes,
    camera_index: int = 0,
) -> tuple[bool, str]:
    """Coba login wajah untuk `username`. Kembalikan (berhasil, pesan)."""
    user = store.get_user_by_username(username)
    if not user or not user.get("face_template"):
        return False, "akun ini belum punya template wajah (jalankan --setup)"

    try:
        template_raw = decrypt_template(db_key, bytes(user["face_template"]))
    except (InvalidTag, ValueError):
        return False, "template wajah rusak/tidak valid"

    bio = FaceBiometrics()
    try:
        bio.load_template(template_raw)
    except Exception:
        return False, "gagal memuat template wajah"

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return False, "webcam tidak tersedia"
    frames = []
    for _ in range(MAX_FRAMES):
        ok, frame = cap.read()
        if ok:
            frames.append(frame)
    cap.release()
    if not frames:
        return False, "gagal membaca frame webcam"

    for frame in frames:
        try:
            if bio.is_match(frame):
                return True, ""
        except RuntimeError:
            continue
    return False, "wajah tidak dikenali"
