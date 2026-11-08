"""Cipher modern: DES/DEA-CBC + AES (Rijndael)-CBC.

Lapis 2 super enkripsi teks (§4.4):
    1. DES/DEA mode CBC (kunci 8 byte = DES tunggal via TripleDES);
    2. AES Rijndael-CBC (kunci 16/24/32 byte; default 32).

Catatan jujur (§9): DES (56-bit efektif) memang usang secara kriptografi;
dipakai sebagai materi tugas dan ditutup oleh AES sebagai lapisan terluar.
Tanpa HMAC — integritas tidak menjadi fokus tab teks: kebenaran kunci
terlihat langsung dari keterbacaan hasil dekripsi.
"""

from __future__ import annotations

import warnings

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_DES_BLOCK = 8
_AES_BLOCK = 16

# Peringatan deprecation dari cryptography untuk TripleDES kunci kecil
# (DES tunggal) sengaja diredam.
_DES_WARNING = (
    DeprecationWarning,
    UserWarning,
)


def _pkcs7_pad(data: bytes, block_size: int) -> bytes:
    pad = block_size - len(data) % block_size
    return data + bytes([pad]) * pad


def _pkcs7_unpad(data: bytes, block_size: int) -> bytes:
    if not data or len(data) % block_size:
        raise ValueError("panjang ciphertext tidak kelipatan blok")
    pad = data[-1]
    if pad < 1 or pad > block_size or data[-pad:] != bytes([pad]) * pad:
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
    if len(key8) != _DES_BLOCK or len(iv8) != _DES_BLOCK:
        raise ValueError("kunci & IV DES harus 8 byte")
    key8 = _set_des_parity(key8)
    padded = _pkcs7_pad(plaintext, _DES_BLOCK)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", _DES_WARNING)
        encryptor = Cipher(algorithms.TripleDES(key8), modes.CBC(iv8)).encryptor()
        return encryptor.update(padded) + encryptor.finalize()


def des_cbc_decrypt(key8: bytes, iv8: bytes, ciphertext: bytes) -> bytes:
    """Invers des_cbc_encrypt."""
    if len(key8) != _DES_BLOCK or len(iv8) != _DES_BLOCK:
        raise ValueError("kunci & IV DES harus 8 byte")
    key8 = _set_des_parity(key8)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", _DES_WARNING)
        decryptor = Cipher(algorithms.TripleDES(key8), modes.CBC(iv8)).decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()
    return _pkcs7_unpad(padded, _DES_BLOCK)


def aes_cbc_encrypt(key: bytes, iv16: bytes, plaintext: bytes) -> bytes:
    """AES Rijndael-CBC + padding PKCS7 (kunci 16/24/32 byte)."""
    if len(key) not in (16, 24, 32):
        raise ValueError("kunci AES harus 16/24/32 byte")
    if len(iv16) != _AES_BLOCK:
        raise ValueError("IV AES harus 16 byte")
    padded = _pkcs7_pad(plaintext, _AES_BLOCK)
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv16)).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def aes_cbc_decrypt(key: bytes, iv16: bytes, ciphertext: bytes) -> bytes:
    """Invers aes_cbc_encrypt."""
    if len(key) not in (16, 24, 32):
        raise ValueError("kunci AES harus 16/24/32 byte")
    if len(iv16) != _AES_BLOCK:
        raise ValueError("IV AES harus 16 byte")
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv16)).decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    return _pkcs7_unpad(padded, _AES_BLOCK)
