-- Skema basis data (SQLite + SQLCipher) — §§4.6 & 5 rancangan.
-- Catatan: seluruh file .db dienkripsi SQLCipher (PRAGMA key saat koneksi).
-- Kolom `isi` dienkripsi AES-GCM per-rekor HANYA bila is_penting = 1.

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    salt_password BLOB NOT NULL,           -- Argon2id salt
    hash_password BLOB NOT NULL,           -- Argon2id hash
    salt_master   BLOB NOT NULL,           -- untuk turunan master key
    dongle_id    TEXT NOT NULL             -- mengikat akun ke dongle
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY,
    owner_id   INTEGER NOT NULL REFERENCES users(id),
    judul      TEXT NOT NULL,
    isi        BLOB,                       -- AES-GCM; hanya bila is_penting=1
    is_penting BOOLEAN NOT NULL DEFAULT 0,
    dibuat_pada TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id          INTEGER PRIMARY KEY,
    nama_aset   TEXT NOT NULL,
    hash_aset   TEXT NOT NULL,             -- SHA-256 berkas/aset
    pemilik     TEXT,
    dicatat_pada TEXT NOT NULL,
    chain_index INTEGER                     -- indeks blok blockchain
);

CREATE TABLE IF NOT EXISTS audit_log (
    id      INTEGER PRIMARY KEY,
    kegiatan TEXT NOT NULL,
    waktu   TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id)
);
