"""Uji super enkripsi teks (TextKeys per-algoritma)."""

from __future__ import annotations

import pytest

from app.core.keys import TextKeys
from app.core.super_encrypt import decrypt_text, encrypt_text

KEYS = TextKeys(
    vigenere=b"LEMON",
    caesar=b"C",
    lfsr=b"SEED1234",
    des=b"DESKEY8!",
    mac=b"MAC-KUNCI-12345678",
)
OTHER_KEYS = TextKeys(
    vigenere=b"ORANGE",
    caesar=b"X",
    lfsr=b"OTHERSEED",
    des=b"RAHAS8!",
    mac=b"MAC-BERBEDA-9999",
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


def test_wrong_key_fails():
    blob = encrypt_text("rahasia", KEYS)
    with pytest.raises(ValueError):
        decrypt_text(blob, OTHER_KEYS)


def test_tampered_blob_fails():
    blob = encrypt_text("jangan diubah", KEYS)
    tampered = blob[:-4] + ("AAAA" if blob[-4:] != "AAAA" else "BBBB")
    with pytest.raises(ValueError):
        decrypt_text(tampered, KEYS)
