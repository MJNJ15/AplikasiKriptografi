"""Uji MessageStore (SQLCipher + enkripsi kolom AES-GCM untuk pesan penting)."""

from __future__ import annotations

import pytest
from cryptography.exceptions import InvalidTag

from app.core.keys import derive_subkey
from app.db.database import Database, MessageStore

COLUMN_KEY = derive_subkey(bytes(range(32)), "db")
DB_KEY = b"K" * 32


@pytest.fixture
def store(tmp_path) -> MessageStore:
    db = Database(str(tmp_path / "messages.db"), DB_KEY)
    return MessageStore(db, COLUMN_KEY)


def test_add_list_roundtrip(store):
    mid = store.add_message(owner_id=1, judul="Penting", isi="rahasia", is_penting=True)
    store.add_message(owner_id=1, judul="Biasa", isi="halo", is_penting=False)
    rows = store.list_messages(1)
    assert len(rows) == 2
    assert rows[0]["judul"] in {"Penting", "Biasa"}
    assert store.get_plain(owner_id=1, message_id=mid) == "rahasia"


def test_important_payload_is_encrypted(store):
    mid = store.add_message(
        owner_id=1, judul="Penting", isi="ini rahasia", is_penting=True
    )
    row = store._db.fetchone("SELECT isi FROM messages WHERE id = ?", (mid,))
    payload = bytes(row["isi"])
    assert payload != b"ini rahasia"
    assert b"rahasia" not in payload


def test_plain_payload_is_readable_bytes(store):
    mid = store.add_message(
        owner_id=1, judul="Biasa", isi="teks biasa", is_penting=False
    )
    row = store._db.fetchone("SELECT isi FROM messages WHERE id = ?", (mid,))
    assert bytes(row["isi"]) == b"teks biasa"


def test_wrong_column_key_fails_on_important(store, tmp_path):
    db = Database(str(tmp_path / "m2.db"), DB_KEY)
    store2 = MessageStore(db, COLUMN_KEY)
    mid = store2.add_message(
        owner_id=1, judul="Penting", isi="rahasia", is_penting=True
    )
    wrong = MessageStore(db, derive_subkey(bytes(range(31, 63)), "db"))
    with pytest.raises(InvalidTag):
        wrong.get_plain(owner_id=1, message_id=mid)


def test_get_missing_message_raises(store):
    with pytest.raises(KeyError):
        store.get_plain(owner_id=1, message_id=999)
