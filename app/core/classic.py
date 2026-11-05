"""Cipher klasik: Vigenère & Caesar.

Lapis 1 super enkripsi teks (§4.4). Keduanya bekerja pada huruf A–Z/a–z;
karakter non-huruf diteruskan tidak berubah (agar tanda baca/spasi utuh).
Kunci diterima sebagai bytes — tiap byte dimodulo 26 menjadi geseran huruf.
"""

from __future__ import annotations

ALPHABET_LEN = 26


def _key_ints(key: bytes) -> list[int]:
    if not key:
        raise ValueError("kunci tidak boleh kosong")
    out: list[int] = []
    for b in key:
        ch = chr(b)
        if "a" <= ch <= "z":
            out.append(ord(ch) - ord("a"))
        elif "A" <= ch <= "Z":
            out.append(ord(ch) - ord("A"))
        else:
            out.append(b % ALPHABET_LEN)
    return out


def vigenere(text: str, key: bytes, encrypt: bool = True) -> str:
    """Enkripsi/dekripsi Vigenère (polialfabetik) pada huruf A–Z.

    Vektor uji klasik: key=b"LEMON", plaintext="ATTACKATDAWN"
    → ciphertext="LXFOPVEFRNHR".
    """
    shifts = _key_ints(key)
    out: list[str] = []
    ki = 0
    direction = 1 if encrypt else -1
    for ch in text:
        upper = ch.upper()
        if "A" <= upper <= "Z":
            base = ord("A") if ch.isupper() else ord("a")
            idx = (ord(upper) - ord("A") + direction * shifts[ki % len(shifts)]) % ALPHABET_LEN
            out.append(chr(base + idx))
            ki += 1
        else:
            out.append(ch)
    return "".join(out)


def caesar(text: str, key: bytes, encrypt: bool = True) -> str:
    """Enkripsi/dekripsi Caesar shift; geseran = jumlah nilai byte kunci mod 26."""
    shift = sum(_key_ints(key)) % ALPHABET_LEN
    if not encrypt:
        shift = -shift
    out: list[str] = []
    for ch in text:
        upper = ch.upper()
        if "A" <= upper <= "Z":
            base = ord("A") if ch.isupper() else ord("a")
            idx = (ord(upper) - ord("A") + shift) % ALPHABET_LEN
            out.append(chr(base + idx))
        else:
            out.append(ch)
    return "".join(out)
