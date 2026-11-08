"""Uji super enkripsi teks (TextKeys per-algoritma)."""

from __future__ import annotations

import pytest

from app.core.keys import TextKeys
from app.core.super_encrypt import decrypt_text, encrypt_text

KEYS = TextKeys(
    vigenere=b"LEMON",
    caesar=b"C",
    des=b"DESKEY8!",
    aes=b"AES-RIJNDAEL-2025",
)
OTHER_KEYS = TextKeys(
    vigenere=b"ORANGE",
    caesar=b"X",
    des=b"RAHAS8!",
    aes=b"AES-LAIN-2026-BERBEDA",
)


def test_roundtrip():
    text = "Pesan rahasia untuk uji super-enkripsi. 123!"
    blob = encrypt_text(text, KEYS)
    assert decrypt_text(blob, KEYS) == text


def test_same_keys_roundtrip_repeatable():
    blob = encrypt_text("pesan yang sama", KEYS)
    assert decrypt_text(blob, KEYS) == "pesan yang sama"

    blob2 = encrypt_text("pesan yang sama", KEYS)
    assert decrypt_text(blob2, KEYS) == "pesan yang sama"


def test_different_keys_give_different_ciphertext():
    a = encrypt_text("pesan yang sama", KEYS)
    b = encrypt_text("pesan yang sama", OTHER_KEYS)
    assert a != b


def test_wrong_key_fails_or_yields_garbage():
    """Tanpa HMAC: kunci salah tidak dijamin memicu exception — hasil
    harus berbeda dari plaintext asli (keterbacaan = penanda kebenaran)."""
    blob = encrypt_text("rahasia", KEYS)
    try:
        out = decrypt_text(blob, OTHER_KEYS)
    except Exception:
        return  # admissible: gagal di dekripsi/UTF-8/padding
    assert out != "rahasia"


def test_tampered_blob_detected_or_yields_garbage():
    blob = encrypt_text("jangan diubah", KEYS)
    tampered = blob[:-4] + ("AAAA" if blob[-4:] != "AAAA" else "BBBB")
    try:
        out = decrypt_text(tampered, KEYS)
    except Exception:
        return  # admissible: gagal di dekripsi/UTF-8/padding
    assert out != "jangan diubah"


def test_short_plaintext_min_length():
    blob = encrypt_text("A", KEYS)
    assert decrypt_text(blob, KEYS) == "A"


def test_unicode_plaintext():
    text = "Pesan dengan aksara: café, 你好, 🔐"
    blob = encrypt_text(text, KEYS)
    assert decrypt_text(blob, KEYS) == text
