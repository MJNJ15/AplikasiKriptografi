"""Uji integrasi boot: provisioning → verifikasi → DB → register → login. """

from __future__ import annotations

from app.core.keys import derive_subkey
from app.db.database import Database, MessageStore, UserStore
from app.security.auth import AuthManager
from app.security.boot import (
    db_key_from_dongle,
    open_boot_database,
    registry_path,
)
from app.security.dongle import find_dongle, load_registry, provision_dongle


def test_db_key_deterministic():
    key = bytes(range(32))
    assert db_key_from_dongle(key) == db_key_from_dongle(key)
    assert db_key_from_dongle(key) != db_key_from_dongle(b"A" * 32)
    assert len(db_key_from_dongle(key)) == 32


def test_provision_then_find(tmp_path):
    drive = tmp_path / "E"
    drive.mkdir()
    reg = tmp_path / "reg.json"
    info = provision_dongle(drive, reg)
    assert (drive / ".dongle.key").exists()
    assert (drive / ".dongle.id").read_text(encoding="utf-8") == info.dongle_id
    found = find_dongle([drive], load_registry(reg))
    assert found.dongle_id == info.dongle_id
    assert found.key == info.key


def test_full_boot_to_message_flow(tmp_path):
    drive = tmp_path / "E"
    drive.mkdir()
    data_dir = tmp_path / "data"
    info = provision_dongle(drive, registry_path(data_dir))
    found = find_dongle([drive], load_registry(registry_path(data_dir)))

    db = open_boot_database(found, data_dir)
    assert isinstance(db, Database)
    store = UserStore(db)
    auth = AuthManager(store)

    auth.register("budi", "rahasia123", info.dongle_id)
    session = auth.login("budi", "rahasia123", found.key)
    assert session.app_key

    column_key = derive_subkey(session.app_key, "db")
    messages = MessageStore(db, column_key)
    mid = messages.add_message(
        owner_id=session.user_id, judul="Catatan", isi="isi rahasia", is_penting=True
    )
    assert messages.get_plain(owner_id=session.user_id, message_id=mid) == "isi rahasia"
    db.close()
