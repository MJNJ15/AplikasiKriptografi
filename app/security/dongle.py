"""Deteksi & verifikasi dongle USB (§4.1).

Alur boot:
    1. temukan drive removable (psutil);
    2. cari `.dongle.key` + `.dongle.id`;
    3. verify ID terhadap registry lokal, lalu SHA-256(key) vs digest;
    4. opsional: challenge-response HMAC-SHA256 (utilitas disediakan).

Jangan hardcode huruf drive — pakai psutil.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import psutil

DONGLE_KEY_FILENAME = ".dongle.key"
DONGLE_ID_FILENAME = ".dongle.id"
DEFAULT_REGISTRY_NAME = "DongleRegistry.json"

_DIGEST_LEN = 32


class DongleError(Exception):
    """Kesalahan umum dongle."""


class DongleMissingError(DongleError):
    """Tidak ditemukan dongle terdaftar."""


class DongleMismatchError(DongleError):
    """Dongle ditemukan tetapi gagal verifikasi."""


@dataclass(frozen=True)
class DongleInfo:
    drive: str
    dongle_id: str
    key: bytes


def discover_removable_drives() -> list[str]:
    """Daftar mountpoint drive removable (tanpa hardcode huruf)."""
    drives: list[str] = []
    for part in psutil.disk_partitions(all=False):
        opts = part.opts.lower()
        if "removable" in opts:
            drives.append(part.mountpoint)
        elif part.fstype and "vfat" in part.fstype.lower():
            drives.append(part.mountpoint)
    return sorted(set(drives))


def load_registry(registry_path: str | Path) -> dict:
    """Baca registry dongle (JSON). Format:
    {"dongle_id": {"digest": "<sha256 hex>"}} atau {"dongle_id": "<sha256 hex>"}.
    """
    path = Path(registry_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _registry_digest(entry: object) -> Optional[str]:
    if isinstance(entry, dict):
        digest = entry.get("digest")
        return digest if isinstance(digest, str) else None
    if isinstance(entry, str):
        return entry
    return None


def read_dongle(drive: str | Path) -> DongleInfo:
    drive_path = Path(drive)
    key_file = drive_path / DONGLE_KEY_FILENAME
    id_file = drive_path / DONGLE_ID_FILENAME
    if not (key_file.exists() and id_file.exists()):
        raise DongleMissingError(f"tidak ada berkas dongle di {drive_path}")
    key = key_file.read_bytes()
    if len(key) < 16:
        raise DongleMismatchError("kunci dongle terlalu pendek")
    dongle_id = id_file.read_text(encoding="utf-8").strip()
    if not dongle_id:
        raise DongleMismatchError("ID dongle kosong")
    return DongleInfo(drive=str(drive_path), dongle_id=dongle_id, key=key)


def verify_dongle(info: DongleInfo, registry: dict) -> bool:
    """Cocokkan ID + SHA-256(key) terhadap registry (constant-time)."""
    entry = registry.get(info.dongle_id)
    digest = _registry_digest(entry)
    if digest is None:
        return False
    actual = hashlib.sha256(info.key).hexdigest()
    return hmac.compare_digest(actual, digest.lower())


def find_dongle(drives, registry: dict) -> DongleInfo:
    """Cari dongle terdaftar di antara drive. Raises DongleError."""
    last_error: Optional[DongleError] = None
    for drive in drives:
        try:
            info = read_dongle(drive)
        except DongleMissingError as exc:
            last_error = exc
            continue
        if info.dongle_id not in registry:
            raise DongleMissingError("ID dongle tidak terdaftar di registry")
        if not verify_dongle(info, registry):
            raise DongleMismatchError("ID dongle ditemukan tetapi digest tidak cocok")
        return info
    raise DongleMissingError("dongle terdaftar tidak ditemukan di drive mana pun")


def hmac_challenge_response(key: bytes, nonce: bytes) -> bytes:
    """Challenge-response HMAC-SHA256 (opsional, penguatan)."""
    return hmac.new(key, nonce, hashlib.sha256).digest()


def provision_dongle(drive: str | Path, registry_path: str | Path) -> DongleInfo:
    """Siapkan flashdisk sebagai dongle: tulis berkas rahasia + daftarkan.

    Menulis `.dongle.key` (32 byte acak) & `.dongle.id` (UUID) ke drive,
    lalu memperbarui registry lokal dengan digest kunci. Idempotent terhadap
    dongle baru (setiap panggilan membuat identitas baru).
    """
    drive_path = Path(drive)
    if not drive_path.is_dir():
        raise DongleMissingError(f"folder drive tidak ditemukan: {drive_path}")
    key = os.urandom(32)
    dongle_id = str(uuid.uuid4())
    (drive_path / DONGLE_KEY_FILENAME).write_bytes(key)
    (drive_path / DONGLE_ID_FILENAME).write_text(dongle_id, encoding="utf-8")

    registry_file = Path(registry_path)
    registry = load_registry(registry_file)
    registry[dongle_id] = {"digest": hashlib.sha256(key).hexdigest()}
    registry_file.parent.mkdir(parents=True, exist_ok=True)
    registry_file.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    return DongleInfo(drive=str(drive_path), dongle_id=dongle_id, key=key)
