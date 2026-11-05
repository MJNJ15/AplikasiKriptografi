"""Uji modul dongle (deteksi, verifikasi, challenge-response)."""

from __future__ import annotations

import hashlib
import os
import uuid

import pytest

from app.security.dongle import (
    DongleMismatchError,
    DongleMissingError,
    discover_removable_drives,
    find_dongle,
    hmac_challenge_response,
    read_dongle,
    verify_dongle,
)


def _make_dongle(drive, dongle_id: str | None = None) -> bytes:
    key = os.urandom(32)
    (drive / ".dongle.key").write_bytes(key)
    (drive / ".dongle.id").write_text(dongle_id or str(uuid.uuid4()), encoding="utf-8")
    return key


def _registry(dongle_id: str, key: bytes) -> dict:
    return {dongle_id: {"digest": hashlib.sha256(key).hexdigest()}}


def test_find_dongle_ok(tmp_path):
    drive = tmp_path / "E"
    drive.mkdir()
    dongle_id = str(uuid.uuid4())
    key = _make_dongle(drive, dongle_id)
    info = find_dongle([drive], _registry(dongle_id, key))
    assert info.dongle_id == dongle_id
    assert info.key == key
    assert verify_dongle(info, _registry(dongle_id, key)) is True


def test_wrong_key_mismatch(tmp_path):
    drive = tmp_path / "E"
    drive.mkdir()
    dongle_id = str(uuid.uuid4())
    _make_dongle(drive, dongle_id)
    # registry memakai digest kunci lain
    other = _registry(dongle_id, os.urandom(32))
    with pytest.raises(DongleMismatchError):
        find_dongle([drive], other)


def test_unknown_id_rejected(tmp_path):
    drive = tmp_path / "E"
    drive.mkdir()
    dongle_id = str(uuid.uuid4())
    _make_dongle(drive, dongle_id)
    with pytest.raises(DongleMissingError):
        find_dongle([drive], {})


def test_missing_files_drive_skipped(tmp_path):
    empty = tmp_path / "D"
    empty.mkdir()
    real = tmp_path / "E"
    real.mkdir()
    dongle_id = str(uuid.uuid4())
    key = _make_dongle(real, dongle_id)
    info = find_dongle([empty, real], _registry(dongle_id, key))
    assert info.drive == str(real)


def test_all_missing_raises(tmp_path):
    empty = tmp_path / "D"
    empty.mkdir()
    with pytest.raises(DongleMissingError):
        find_dongle([empty], {})


def test_read_dongle_short_key_rejected(tmp_path):
    drive = tmp_path / "E"
    drive.mkdir()
    (drive / ".dongle.key").write_bytes(b"pendek")
    (drive / ".dongle.id").write_text(str(uuid.uuid4()), encoding="utf-8")
    with pytest.raises(DongleMismatchError):
        read_dongle(drive)


def test_hmac_challenge_response():
    key = b"K" * 32
    nonce = b"N" * 16
    tag = hmac_challenge_response(key, nonce)
    assert tag == hmac_challenge_response(key, nonce)
    assert tag != hmac_challenge_response(key, b"M" * 16)
    assert len(tag) == 32


def test_discover_returns_list():
    assert isinstance(discover_removable_drives(), list)
