"""Koneksi & akses basis data SQLCipher.

§4.6: seluruh file .db dienkripsi SQLCipher (PRAGMA key saat koneksi);
kolom sensitif (mis. face_template) dienkripsi AES-GCM oleh pemanggil.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlcipher3 import dbapi2 as sqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    salt_password BLOB NOT NULL,
    hash_password BLOB NOT NULL,
    face_template BLOB,
    salt_master   BLOB NOT NULL,
    dongle_id    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY,
    owner_id   INTEGER NOT NULL REFERENCES users(id),
    judul      TEXT NOT NULL,
    isi        BLOB,
    is_penting BOOLEAN NOT NULL DEFAULT 0,
    dibuat_pada TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id          INTEGER PRIMARY KEY,
    nama_aset   TEXT NOT NULL,
    hash_aset   TEXT NOT NULL,
    pemilik     TEXT,
    dicatat_pada TEXT NOT NULL,
    chain_index INTEGER
);

CREATE TABLE IF NOT EXISTS audit_log (
    id      INTEGER PRIMARY KEY,
    kegiatan TEXT NOT NULL,
    waktu   TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id)
);
"""


def _open_connection(path: str, key: bytes) -> sqlite.Connection:
    conn = sqlite.connect(path)
    # SQLCipher: kunci sebagai passphrase (hex) dalam kutip string.
    conn.execute(f"PRAGMA key = '{key.hex()}'")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


class Database:
    """Pembungkus tipis koneksi SQLCipher."""

    def __init__(self, path: str, key: bytes) -> None:
        self._conn = _open_connection(path, key)
        self._conn.row_factory = sqlite.Row

    def exists(self, sql: str, params: tuple = ()) -> bool:
        row = self._conn.execute(sql, params).fetchone()
        return row is not None

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite.Row]:
        return self._conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> list:
        return self._conn.execute(sql, params).fetchall()

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._conn.execute(sql, params)
        self._conn.commit()

    def insert(self, sql: str, params: tuple = ()) -> int:
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return int(cur.lastrowid)

    def close(self) -> None:
        self._conn.close()


class UserStore:
    """Operasi tabel `users`."""

    def __init__(self, db: Database) -> None:
        self._db = db

    def insert_user(
        self,
        *,
        username: str,
        salt_password: bytes,
        hash_password: bytes,
        face_template: Optional[bytes],
        salt_master: bytes,
        dongle_id: str,
    ) -> None:
        self._db.execute(
            """
            INSERT INTO users (username, salt_password, hash_password, face_template,
                               salt_master, dongle_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, salt_password, hash_password, face_template, salt_master, dongle_id),
        )

    def get_user_by_username(self, username: str) -> Optional[dict]:
        row = self._db.fetchone("SELECT * FROM users WHERE username = ?", (username,))
        return dict(row) if row else None

    def list_users(self) -> list[dict]:
        rows = self._db.fetchall("SELECT id, username FROM users ORDER BY id")
        return [dict(r) for r in rows]

    def set_face_template(self, user_id: int, face_template: bytes) -> None:
        self._db.execute("UPDATE users SET face_template = ? WHERE id = ?", (face_template, user_id))


class MessageStore:
    """Operasi tabel `messages`, dengan enkripsi kolom AES-GCM untuk pesan penting.

    §4.6 / keputusan #4: hanya rekor `is_penting=1` yang isinya dienkripsi
    ganda (AES-GCM per-rekor). Pesan biasa tetap terlindungi lapis SQLCipher.
    """

    NONCE_LEN = 12

    def __init__(self, db: Database, column_key: bytes) -> None:
        self._db = db
        self._cipher = AESGCM(column_key)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def add_message(
        self,
        *,
        owner_id: int,
        judul: str,
        isi: str,
        is_penting: bool,
        dibuat_pada: str | None = None,
    ) -> int:
        if is_penting:
            nonce = os.urandom(self.NONCE_LEN)
            ct = self._cipher.encrypt(nonce, isi.encode("utf-8"), None)
            payload = nonce + ct
        else:
            payload = isi.encode("utf-8")
        cur = self._db.insert(
            """
            INSERT INTO messages (owner_id, judul, isi, is_penting, dibuat_pada)
            VALUES (?, ?, ?, ?, ?)
            """,
            (owner_id, judul, payload, int(is_penting), dibuat_pada or self._now_iso()),
        )
        return cur

    def list_messages(self, owner_id: int) -> list[dict]:
        rows = self._db.fetchall(
            """
            SELECT id, judul, is_penting, dibuat_pada FROM messages
            WHERE owner_id = ? ORDER BY id DESC
            """,
            (owner_id,),
        )
        return [dict(r) for r in rows]

    def get_plain(self, *, owner_id: int, message_id: int) -> str:
        row = self._db.fetchone(
            "SELECT isi, is_penting FROM messages WHERE id = ? AND owner_id = ?",
            (message_id, owner_id),
        )
        if row is None:
            raise KeyError("pesan tidak ditemukan")
        payload = bytes(row["isi"]) if row["isi"] is not None else b""
        if row["is_penting"]:
            if len(payload) < self.NONCE_LEN + 16:
                raise ValueError("blob pesan penting tidak valid")
            nonce, ct = payload[: self.NONCE_LEN], payload[self.NONCE_LEN :]
            return self._cipher.decrypt(nonce, ct, None).decode("utf-8")
        return payload.decode("utf-8")

    def get_payload(self, *, owner_id: int, message_id: int) -> tuple[bytes, bool]:
        """Kembalikan (payload mentah yang tersimpan, is_penting)."""
        row = self._db.fetchone(
            "SELECT isi, is_penting FROM messages WHERE id = ? AND owner_id = ?",
            (message_id, owner_id),
        )
        if row is None:
            raise KeyError("pesan tidak ditemukan")
        payload = bytes(row["isi"]) if row["isi"] is not None else b""
        return payload, bool(row["is_penting"])
