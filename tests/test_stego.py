"""Uji steganografi LSB + permutasi (§4.8)."""

from __future__ import annotations

import numpy as np
import pytest

from app.core.stego import capacity, embed_message, extract_message

KEY = b"kata-sandi-stego"
OTHER_KEY = b"kunci-lain"


def _cover(h: int = 80, w: int = 80) -> np.ndarray:
    rng = np.random.default_rng(7)
    return rng.integers(0, 256, (h, w, 3), dtype=np.uint8)


def test_roundtrip():
    cover = _cover()
    message = b"STEGO rahasia 123!"
    stego = embed_message(cover, message, KEY)
    assert extract_message(stego, KEY) == message


def test_various_messages():
    cover = _cover()
    for msg in (b"a", b"x" * 64, bytes(range(256)) * 2):
        stego = embed_message(cover, msg, KEY)
        assert extract_message(stego, KEY) == msg


def test_stego_differs_but_close():
    cover = _cover()
    stego = embed_message(cover, b"pesan", KEY)
    assert not np.array_equal(cover, stego)
    # hanya LSB yang berubah → selisih absolut kecil
    diff = np.abs(cover.astype(int) - stego.astype(int))
    assert diff.max() <= 1


def test_message_too_large():
    small = _cover(h=8, w=8)  # kapasitas 192 bit
    with pytest.raises(ValueError):
        embed_message(small, b"Z" * 100, KEY)


def test_wrong_key_fails_or_garbage():
    cover = _cover()
    message = b"pesan penting"
    stego = embed_message(cover, message, KEY)
    try:
        out = extract_message(stego, OTHER_KEY)
    except ValueError:
        return  # expected path
    assert out != message


def test_capacity_formula():
    img = _cover(10, 20)
    assert capacity(img) == 10 * 20 * 3
