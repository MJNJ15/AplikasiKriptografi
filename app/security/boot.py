"""Orkestrasi boot aplikasi (fase 5).

Alur: verifikasi dongle → buka basis data SQLCipher (kunci DB diturunkan
dari kunci dongle, tersedia sebelum login) → lanjut ke login.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from ..db.database import Database
from ..utils.paths import paths_dir
from .dongle import (
    DEFAULT_REGISTRY_NAME,
    DongleInfo,
    discover_removable_drives,
    find_dongle,
    load_registry,
)

DB_KEY_INFO = b"app-db-key-v1"
DATABASE_FILENAME = "aplikasi.db"


def db_key_from_dongle(dongle_key: bytes) -> bytes:
    """Kunci SQLCipher (32 byte) diturunkan dari kunci dongle."""
    return hashlib.sha256(dongle_key + DB_KEY_INFO).digest()


def registry_path(data_dir: Optional[Path] = None) -> Path:
    return (data_dir if data_dir is not None else paths_dir()) / DEFAULT_REGISTRY_NAME


def database_path(data_dir: Optional[Path] = None) -> Path:
    return (data_dir if data_dir is not None else paths_dir()) / DATABASE_FILENAME


def ensure_data_dir(data_dir: Optional[Path] = None) -> Path:
    target = data_dir if data_dir is not None else paths_dir()
    target.mkdir(parents=True, exist_ok=True)
    return target


def boot_with_dongle(data_dir: Optional[Path] = None) -> DongleInfo:
    """Temukan & verifikasi dongle. Raises `DongleError` bila gagal."""
    return find_dongle(discover_removable_drives(), load_registry(registry_path(data_dir)))


def open_boot_database(info: DongleInfo, data_dir: Optional[Path] = None) -> Database:
    """Buka DB terenkripsi dengan kunci turunan dari dongle ini."""
    target = ensure_data_dir(data_dir)
    return Database(str(database_path(target)), db_key_from_dongle(info.key))
