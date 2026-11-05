"""Uji enkripsi file (ChaCha20-Poly1305)."""

from __future__ import annotations

import pytest

from cryptography.exceptions import InvalidTag

from app.core.file_crypto import decrypt_data, encrypt_data

KEY = bytes(range(32))


def test_data_roundtrip():
    for payload in (b"", b"a", b"x" * 1000, bytes(range(256)) * 4):
        blob = encrypt_data(payload, KEY)
        assert decrypt_data(blob, KEY) == payload


def test_wrong_key_fails():
    blob = encrypt_data(b"rahasia", KEY)
    bad = bytes(x ^ 0xFF for x in KEY)
    with pytest.raises(InvalidTag):
        decrypt_data(blob, bad)


def test_tampered_fails():
    blob = bytearray(encrypt_data(b"data penting", KEY))
    blob[-1] ^= 0x01
    with pytest.raises(InvalidTag):
        decrypt_data(bytes(blob), KEY)
