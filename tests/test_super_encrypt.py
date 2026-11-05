"""Uji super enkripsi teks."""

from __future__ import annotations

import pytest

from app.core.keys import make_text_keys
from app.core.super_encrypt import decrypt_text, encrypt_text

APP_KEY = bytes(range(32))
BAD_APP_KEY = bytes(0xFF ^ i for i in range(32))


def test_roundtrip():
    classic_key, des_key, mac_key = make_text_keys(APP_KEY)
    text = "Pesan rahasia untuk uji super-enkripsi. 123!"
    blob = encrypt_text(text, classic_key, des_key, mac_key)
    assert decrypt_text(blob, classic_key, des_key, mac_key) == text


def test_ciphertext_nondeterministic():
    keys = make_text_keys(APP_KEY)
    text = "pesan yang sama"
    a = encrypt_text(text, *keys)
    b = encrypt_text(text, *keys)
    assert a != b


def test_wrong_key_fails():
    good = make_text_keys(APP_KEY)
    bad = make_text_keys(BAD_APP_KEY)
    blob = encrypt_text("rahasia", *good)
    with pytest.raises(ValueError):
        decrypt_text(blob, *bad)


def test_tampered_blob_fails():
    keys = make_text_keys(APP_KEY)
    blob = encrypt_text("jangan diubah", *keys)
    tampered = blob[:-4] + ("AAAA" if blob[-4:] != "AAAA" else "BBBB")
    with pytest.raises(ValueError):
        decrypt_text(tampered, *keys)
