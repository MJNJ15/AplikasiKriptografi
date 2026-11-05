"""Super enkripsi teks (klasik → modern).

Alur (§4.4):
    Vigenère → Caesar → XOR-LFSR → DES/DEA-CBC → HMAC-SHA256
Hasil akhir (Base64) = seed_lfsr(16) ‖ iv_des(8) ‖ ciphertext ‖ hmac(32).

Kunci (classic/des/mac) diturunkan oleh `keys.make_text_keys` dari kunci
aplikasi; seed LFSR dibuat acak per-enkripsi sehingga ciphertext untuk pesan
yang sama berbeda (non-deterministik).
"""

from __future__ import annotations

import base64
import hmac
import os

from . import classic, modern

LFSR_SEED_LEN = 16
DES_IV_LEN = 8
HMAC_LEN = 32
HEADER_LEN = LFSR_SEED_LEN + DES_IV_LEN


def _sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, digestmod="sha256").digest()


def encrypt_text(plaintext: str, classic_key: bytes, des_key: bytes, mac_key: bytes) -> str:
    """Super enkripsi: str → Base64."""
    # Lapis 1 — klasik (Vigenère → Caesar)
    layer1 = classic.vigenere(plaintext, classic_key, encrypt=True)
    layer2 = classic.caesar(layer1, classic_key, encrypt=True)
    data = layer2.encode("utf-8")

    # Lapis 2 — modern (LFSR XOR → DES-CBC → HMAC)
    seed = os.urandom(LFSR_SEED_LEN)
    stream = modern.lfsr_keystream(seed, len(data))
    xored = modern.xor_bytes(data, stream)

    iv = os.urandom(DES_IV_LEN)
    ct = modern.des_cbc_encrypt(des_key, iv, xored)

    tag = _sha256(mac_key, iv + ct)
    bundle = seed + iv + ct + tag
    return base64.b64encode(bundle).decode("ascii")


def decrypt_text(b64: str, classic_key: bytes, des_key: bytes, mac_key: bytes) -> str:
    """Super enkripsi invers: Base64 → str. Gagal bila MAC tidak cocok."""
    bundle = base64.b64decode(b64.encode("ascii"))
    if len(bundle) < HEADER_LEN + HMAC_LEN + modern._BLOCK_SIZE:
        raise ValueError("blob hasil enkripsi tidak valid (terlalu pendek)")

    seed = bundle[:LFSR_SEED_LEN]
    iv = bundle[LFSR_SEED_LEN:HEADER_LEN]
    ct = bundle[HEADER_LEN:-HMAC_LEN]
    tag = bundle[-HMAC_LEN:]

    expected = _sha256(mac_key, iv + ct)
    if not hmac.compare_digest(tag, expected):
        raise ValueError("tag HMAC tidak cocok — kunci salah atau data diubah")

    xored = modern.des_cbc_decrypt(des_key, iv, ct)
    stream = modern.lfsr_keystream(seed, len(xored))
    data = modern.xor_bytes(xored, stream)

    layer2 = data.decode("utf-8")
    layer1 = classic.caesar(layer2, classic_key, encrypt=False)
    return classic.vigenere(layer1, classic_key, encrypt=False)
