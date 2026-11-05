"""Manajemen kunci & KDF (Argon2id, HKDF) — placeholder, belum diimplementasikan.

Mengikuti §4.7 rancangan:
    master_key = Argon2id(kata_sandi, salt_master)
    kunci_aplikasi = HKDF-SHA256(dongle.key || master_key, info="app-master")
Sub-kunci per fitur diturunkan dengan `info` berbeda (text-des, text-lfsr,
text-mac, text-classic, file-chacha, db-sqlcipher, img-stego, asset-chain).
"""

from __future__ import annotations
