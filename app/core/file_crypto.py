"""Enkripsi file ChaCha20-Poly1305.

Kriteria 4: file dienkripsi dengan kriptografi berbeda dari teks (bukan AES).
Hasil biner = nonce(12) ‖ ciphertext ‖ tag(16); ekstensi `.enc` ditangani
lapisan UI. Core ini bekerja pada bytes dan path.
"""

from __future__ import annotations

import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

NONCE_LEN = 12
KEY_LEN = 32


def encrypt_data(data: bytes, key32: bytes) -> bytes:
    """Enkripsi bytes → nonce ‖ ciphertext ‖ tag."""
    if len(key32) != KEY_LEN:
        raise ValueError(f"kunci ChaCha20 harus {KEY_LEN} byte")
    nonce = os.urandom(NONCE_LEN)
    ct = ChaCha20Poly1305(key32).encrypt(nonce, data, None)
    return nonce + ct


def decrypt_data(blob: bytes, key32: bytes) -> bytes:
    """Dekripsi kebalikan encrypt_data. Salah kunci/rusak → InvalidTag."""
    if len(key32) != KEY_LEN:
        raise ValueError(f"kunci ChaCha20 harus {KEY_LEN} byte")
    if len(blob) < NONCE_LEN + 16:
        raise ValueError("blob hasil enkripsi tidak valid (terlalu pendek)")
    nonce, ct = blob[:NONCE_LEN], blob[NONCE_LEN:]
    return ChaCha20Poly1305(key32).decrypt(nonce, ct, None)


def encrypt_file(src: str | Path, dst: str | Path, key32: bytes) -> Path:
    src, dst = Path(src), Path(dst)
    encrypted = encrypt_data(src.read_bytes(), key32)
    dst.write_bytes(encrypted)
    return dst


def decrypt_file(src: str | Path, dst: str | Path, key32: bytes) -> Path:
    src, dst = Path(src), Path(dst)
    plain = decrypt_data(src.read_bytes(), key32)
    dst.write_bytes(plain)
    return dst
