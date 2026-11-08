"""Uji penyimpanan template wajah terenkripsi (AES-GCM)."""

from __future__ import annotations

import pytest

from cryptography.exceptions import InvalidTag

from app.core.keys import derive_subkey
from app.db.database import Database, UserStore
from app.security.face_login import (
    decrypt_template,
    encrypt_template,
    load_face_template,
    store_face_template,
)

DB_KEY = bytes(range(32))
COLUMN_KEY = derive_subkey(bytes(range(32)), "db")
TEMPLATE = b"\x9a\x81" * 128  # dummy embedding serialized


@pytest.fixture
def store(tmp_path) -> UserStore:
    db = Database(str(tmp_path / "face.db"), DB_KEY)
    return UserStore(db)


def _register(store, username="budi"):
    db = store._db
    salt = b"s" * 16
    store.insert_user(
        username=username,
        salt_password=salt,
        hash_password=b"h" * 32,
        salt_master=salt,
        dongle_id="dongle-1",
    )
    return store.get_user_by_username(username)["id"]


def test_encrypt_decrypt_roundtrip():
    blob = encrypt_template(DB_KEY, TEMPLATE)
    assert blob != TEMPLATE
    assert decrypt_template(DB_KEY, blob) == TEMPLATE


def test_wrong_key_fails():
    blob = encrypt_template(DB_KEY, TEMPLATE)
    with pytest.raises(InvalidTag):
        decrypt_template(b"X" * 32, blob)


def test_store_and_load(store):
    user_id = _register(store)
    store_face_template(store, user_id, DB_KEY, TEMPLATE)
    loaded = load_face_template(store, "budi", DB_KEY)
    assert loaded == TEMPLATE


def test_load_without_template_raises(store):
    _register(store)
    with pytest.raises(ValueError):
        load_face_template(store, "budi", DB_KEY)
