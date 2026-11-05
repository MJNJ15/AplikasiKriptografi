"""Cipher modern: LFSR, DES/DEA, HMAC.

Lapis 2 super enkripsi teks (§4.4):
    1. keystream LFSR (XOR dengan data);
    2. DES/DEA mode CBC (kunci 8 byte = DES tunggal via TripleDES);
    3. tag HMAC-SHA256 untuk autentikasi.

Catatan jujur (§9): DES (56-bit efektif) & LFSR memang usang secara
kriptografi; dipakai sebagai materi tugas. HMAC menutup kekurangan
autentikasi DES/LFSR.
"""

from __future__ import annotations

import hmac
import warnings

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_BLOCK_SIZE = 8  # DES block (byte)

# Peringatan deprecation dari cryptography untuk TripleDES kunci kecil
# (DES tunggal) sengaja diredam.
_DES_WARNING = (
    DeprecationWarning,
    UserWarning,
)


class LFSR:
    """Pembangkit keystream LFSR (Galois, 32-bit).

    Representasi Galois: state digeser ke kanan; bila bit yang keluar
    bernilai 1, state di-XOR dengan mask POLY. Deterministik terhadap seed;
    seed berbeda → keystream berbeda. Catatan: LFSR bersifat linear —
    lihat keterbatasan di §9.
    """

    WIDTH = 32
    MASK = 0xFFFFFFFF
    POLY = 0xB4BCD35C

    def __init__(self, seed: bytes) -> None:
        if len(seed) < 4:
            raise ValueError("seed LFSR minimal 4 byte")
        state = int.from_bytes(seed[:4], "big") & self.MASK
        self._state = state or 1  # state nol dilarang

    def next_bit(self) -> int:
        lsb = self._state & 1
        self._state >>= 1
        if lsb:
            self._state ^= self.POLY
        return lsb

    def keystream(self, length: int) -> bytes:
        out = bytearray()
        for _ in range(length):
            byte = 0
            for _ in range(8):
                byte = (byte << 1) | self.next_bit()
            out.append(byte)
        return bytes(out)


def lfsr_keystream(seed: bytes, length: int) -> bytes:
    return LFSR(seed).keystream(length)


def xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("panjang a dan b harus sama untuk XOR")
    return bytes(x ^ y for x, y in zip(a, b))


def _pkcs7_pad(data: bytes) -> bytes:
    pad = _BLOCK_SIZE - len(data) % _BLOCK_SIZE
    return data + bytes([pad]) * pad


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data or len(data) % _BLOCK_SIZE:
        raise ValueError("panjang ciphertext tidak kelipatan blok DES")
    pad = data[-1]
    if pad < 1 or pad > _BLOCK_SIZE or data[-pad:] != bytes([pad]) * pad:
        raise ValueError("padding PKCS7 tidak valid")
    return data[:-pad]


def _set_des_parity(key8: bytes) -> bytes:
    """Koreksi bit paritas ganjil per byte (syarat kunci DES)."""
    out = bytearray()
    for b in key8:
        if bin(b).count("1") % 2 == 0:
            b ^= 0x01
        out.append(b)
    return bytes(out)


def des_cbc_encrypt(key8: bytes, iv8: bytes, plaintext: bytes) -> bytes:
    """DES/DEA-CBC + padding PKCS7 (kunci 8 byte = DES tunggal)."""
    if len(key8) != _BLOCK_SIZE or len(iv8) != _BLOCK_SIZE:
        raise ValueError("kunci & IV DES harus 8 byte")
    key8 = _set_des_parity(key8)
    padded = _pkcs7_pad(plaintext)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", _DES_WARNING)
        encryptor = Cipher(algorithms.TripleDES(key8), modes.CBC(iv8)).encryptor()
        return encryptor.update(padded) + encryptor.finalize()


def des_cbc_decrypt(key8: bytes, iv8: bytes, ciphertext: bytes) -> bytes:
    """Invers des_cbc_encrypt."""
    if len(key8) != _BLOCK_SIZE or len(iv8) != _BLOCK_SIZE:
        raise ValueError("kunci & IV DES harus 8 byte")
    key8 = _set_des_parity(key8)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", _DES_WARNING)
        decryptor = Cipher(algorithms.TripleDES(key8), modes.CBC(iv8)).decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
    return _pkcs7_unpad(padded)


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashes.SHA256).digest()
