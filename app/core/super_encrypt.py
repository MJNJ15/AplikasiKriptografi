"""Super enkripsi teks (klasik → modern) — §4.4.

Alur:
    Vigenère(kunci) → Caesar(kunci) → DES/DEA-CBC(kunci)
    → AES Rijndael-CBC(kunci)

Setiap algoritma memakai kunci masukannya sendiri (TextKeys). Hasil akhir
(Base64) = iv_des(8) ‖ iv_aes(16) ‖ ciphertext. IV acak per-operasi;
tanpa tag HMAC — integritas bukan fokus (kebenaran kunci terlihat dari
keterbacaan hasil dekripsi).
"""

from __future__ import annotations

import base64
import os

from . import classic, modern
from .keys import TextKeys, derive_aes_key, derive_des_key

DES_IV_LEN = 8
AES_IV_LEN = 16
HEADER_LEN = DES_IV_LEN + AES_IV_LEN


def encrypt_text(plaintext: str, keys: TextKeys) -> str:
    """Super enkripsi: str → Base64 (kunci per-algoritma)."""
    # Lapis 1 — klasik (Vigenère → Caesar)
    layer1 = classic.vigenere(plaintext, keys.vigenere, encrypt=True)
    layer2 = classic.caesar(layer1, keys.caesar, encrypt=True)
    data = layer2.encode("utf-8")

    # Lapis 2 — modern (DES-CBC → AES-CBC)
    iv_des = os.urandom(DES_IV_LEN)
    ct_des = modern.des_cbc_encrypt(derive_des_key(keys.des), iv_des, data)

    iv_aes = os.urandom(AES_IV_LEN)
    ct_aes = modern.aes_cbc_encrypt(derive_aes_key(keys.aes), iv_aes, ct_des)

    bundle = iv_des + iv_aes + ct_aes
    return base64.b64encode(bundle).decode("ascii")


def decrypt_text(b64: str, keys: TextKeys) -> str:
    """Super enkripsi invers: Base64 → str."""
    bundle = base64.b64decode(b64.encode("ascii"))
    if len(bundle) < HEADER_LEN + 16:
        raise ValueError("blob hasil enkripsi tidak valid (terlalu pendek)")

    iv_des = bundle[:DES_IV_LEN]
    iv_aes = bundle[DES_IV_LEN:HEADER_LEN]
    ct_aes = bundle[HEADER_LEN:]

    ct_des = modern.aes_cbc_decrypt(derive_aes_key(keys.aes), iv_aes, ct_aes)
    data = modern.des_cbc_decrypt(derive_des_key(keys.des), iv_des, ct_des)

    layer2 = data.decode("utf-8")
    layer1 = classic.caesar(layer2, keys.caesar, encrypt=False)
    return classic.vigenere(layer1, keys.vigenere, encrypt=False)
