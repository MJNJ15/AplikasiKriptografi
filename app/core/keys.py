"""Manajemen kunci & KDF (Argon2id, HKDF).

Mengikuti §4.7 rancangan:
    master_key        = Argon2id(kata_sandi, salt_master)
    kunci_aplikasi    = HKDF-SHA256(dongle.key || master_key, info="app-master")
    sub-kunci per fitur = HKDF-SHA256(kunci_aplikasi, info=<nama>)

Argon2id dipakai dengan parameter yang disarankan OWASP (memory 64 MiB,
time 3, parallelism 4) — dapat disesuaikan bila terlalu berat untuk uji.
"""

from __future__ import annotations

import os

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

ARGON2_MEMORY_KIB = 64 * 1024  # 64 MiB
ARGON2_TIME = 3
ARGON2_PARALLELISM = 4
DEFAULT_KEY_LEN = 32

# Nama sub-kunci → `info` HKDF (lihat tabel §4.7).
SUBKEY_INFO: dict[str, bytes] = {
    "des": b"text-des",
    "lfsr": b"text-lfsr",
    "mac": b"text-mac",
    "classic": b"text-classic",
    "chacha": b"file-chacha",
    "db": b"db-sqlcipher",
    "stego": b"img-stego",
    "chain": b"asset-chain",
}


def generate_salt(length: int = 16) -> bytes:
    """Salt acak untuk KDF (16 byte default)."""
    return os.urandom(length)


def _argon2_kdf(salt: bytes, length: int) -> Argon2id:
    return Argon2id(
        salt=salt,
        length=length,
        iterations=ARGON2_TIME,
        lanes=ARGON2_PARALLELISM,
        memory_cost=ARGON2_MEMORY_KIB,
    )


def argon2id_hash(password: str, salt: bytes, length: int = DEFAULT_KEY_LEN) -> bytes:
    """Hash kata sandi dengan Argon2id (untuk penyimpanan & verifikasi)."""
    return _argon2_kdf(salt, length).derive(password.encode("utf-8"))


def verify_password(password: str, salt: bytes, expected_hash: bytes) -> bool:
    """Verifikasi kata sandi terhadap hash Argon2id (constant-time)."""
    try:
        _argon2_kdf(salt, len(expected_hash)).verify(password.encode("utf-8"), expected_hash)
    except InvalidKey:
        return False
    return True


def derive_master_key(password: str, salt_master: bytes) -> bytes:
    """Master key murni dari kata sandi (belum dicampur dongle)."""
    return argon2id_hash(password, salt_master)


def mix_with_dongle(master_key: bytes, dongle_key: bytes) -> bytes:
    """kunci_aplikasi = HKDF-SHA256(dongle.key || master_key, info="app-master")."""
    ikm = dongle_key + master_key
    hkdf = HKDF(algorithm=hashes.SHA256(), length=DEFAULT_KEY_LEN, salt=None, info=b"app-master")
    return hkdf.derive(ikm)


def derive_subkey(app_key: bytes, name: str, length: int = DEFAULT_KEY_LEN) -> bytes:
    """Turunkan sub-kunci per fitur dari kunci aplikasi (info berbeda)."""
    if name not in SUBKEY_INFO:
        raise ValueError(f"sub-kunci tak dikenal: {name!r}")
    hkdf = HKDF(algorithm=hashes.SHA256(), length=length, salt=None, info=SUBKEY_INFO[name])
    return hkdf.derive(app_key)


def make_text_keys(app_key: bytes) -> tuple[bytes, bytes, bytes]:
    """Sub-kunci super enkripsi teks: (classic, des, mac)."""
    return (
        derive_subkey(app_key, "classic", length=16),
        derive_subkey(app_key, "des", length=8),
        derive_subkey(app_key, "mac", length=32),
    )
