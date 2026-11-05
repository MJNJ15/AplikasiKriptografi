"""Uji cipher klasik (Vigenère, Caesar)."""

from __future__ import annotations

import pytest

from app.core.classic import caesar, vigenere


def test_vigenere_known_vector():
    # Vektor klasik: key LEMON, plaintext ATTACKATDAWN → LXFOPVEFRNHR
    assert vigenere("ATTACKATDAWN", b"LEMON", encrypt=True) == "LXFOPVEFRNHR"
    assert vigenere("LXFOPVEFRNHR", b"LEMON", encrypt=False) == "ATTACKATDAWN"


def test_vigenere_roundtrip_preserves_case_and_nonalpha():
    text = "Hello, Dunia! 123"
    key = b"rahasia"
    enc = vigenere(text, key)
    assert enc != text
    assert vigenere(enc, key, encrypt=False) == text


def test_caesar_roundtrip():
    text = "ABC DEF xyz"
    key = b"kunci"
    enc = caesar(text, key)
    assert caesar(enc, key, encrypt=False) == text


def test_empty_key_rejected():
    with pytest.raises(ValueError):
        vigenere("ABC", b"")
