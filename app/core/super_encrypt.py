"""Super enkripsi teks (klasik → modern) — §4.4.

Alur:
    Vigenère(kunci) → Caesar(kunci) → XOR-LFSR(seed kunci)
    → DES/DEA-CBC(kunci) → HMAC-SHA256(kunci)

Setiap algoritma memakai kunci masukannya sendiri (TextKeys). Hasil akhir
(Base64) = iv_des(8) ‖ ciphertext ‖ hmac(32). Deterministik: kunci sama →
ciphertext sama (seed LFSR berasal dari kunci).
"""

from __future__ import annotations

import base64
import hmac
import os

from . import classic, modern
from .keys import TextKeys, derive_des_key

DES_IV_LEN = 8
HMAC_LEN = 32
HEADER_LEN = DES_IV_LEN


def _sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, digestmod="sha256").digest()


def encrypt_text(plaintext: str, keys: TextKeys) -> str:
    """Super enkripsi: str → Base64 (kunci per-algoritma)."""
    # Lapis 1 — klasik (Vigenère → Caesar)
    layer1 = classic.vigenere(plaintext, keys.vigenere, encrypt=True)
    layer2 = classic.caesar(layer1, keys.caesar, encrypt=True)
    data = layer2.encode("utf-8")

    # Lapis 2 — modern (LFSR XOR → DES-CBC → HMAC)
    stream = modern.lfsr_keystream(keys.lfsr, len(data))
    xored = modern.xor_bytes(data, stream)

    iv = os.urandom(DES_IV_LEN)
    ct = modern.des_cbc_encrypt(derive_des_key(keys.des), iv, xored)

    tag = _sha256(keys.mac, iv + ct)
    bundle = iv + ct + tag
    return base64.b64encode(bundle).decode("ascii")


def decrypt_text(b64: str, keys: TextKeys) -> str:
    """Super enkripsi invers: Base64 → str. Gagal bila MAC tidak cocok."""
    bundle = base64.b64decode(b64.encode("ascii"))
    if len(bundle) < HEADER_LEN + HMAC_LEN + modern._BLOCK_SIZE:
        raise ValueError("blob hasil enkripsi tidak valid (terlalu pendek)")

    iv = bundle[:HEADER_LEN]
    ct = bundle[HEADER_LEN:-HMAC_LEN]
    tag = bundle[-HMAC_LEN:]

    expected = _sha256(keys.mac, iv + ct)
    if not hmac.compare_digest(tag, expected):
        raise ValueError("tag HMAC tidak cocok — kunci salah atau data diubah")

    xored = modern.des_cbc_decrypt(derive_des_key(keys.des), iv, ct)
    stream = modern.lfsr_keystream(keys.lfsr, len(xored))
    data = modern.xor_bytes(xored, stream)

    layer2 = data.decode("utf-8")
    layer1 = classic.caesar(layer2, keys.caesar, encrypt=False)
    return classic.vigenere(layer1, keys.vigenere, encrypt=False)
