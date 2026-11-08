"""Penyimpanan & perbandingan template wajah (enkripsi AES-GCM).

Template (embedding 128-d / `FaceBiometrics.save_template`) disimpan
terenkripsi AES-GCM di kolom `users.face_template`. Kunci = kunci DB
yang diturunkan dari dongle.
"""

from __future__ import annotations

import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..db.database import UserStore
from .biometric import FaceBiometrics

NONCE_LEN = 12


def encrypt_template(db_key: bytes, template: bytes) -> bytes:
    nonce = os.urandom(NONCE_LEN)
    return nonce + AESGCM(db_key).encrypt(nonce, template, None)


def decrypt_template(db_key: bytes, blob: bytes) -> bytes:
    if len(blob) < NONCE_LEN + 16:
        raise ValueError("template terenkripsi tidak valid")
    nonce, ct = blob[:NONCE_LEN], blob[NONCE_LEN:]
    return AESGCM(db_key).decrypt(nonce, ct, None)


def store_face_template(store: UserStore, user_id: int, db_key: bytes, template: bytes) -> None:
    store.set_face_template(user_id, encrypt_template(db_key, template))


def load_face_template(store: UserStore, username: str, db_key: bytes) -> bytes:
    """Dekripsi template wajah milik `username`. Raises bila tidak ada/rusak."""
    user = store.get_user_by_username(username)
    if not user or not user.get("face_template"):
        raise ValueError("akun ini belum punya template wajah")
    return decrypt_template(db_key, bytes(user["face_template"]))
