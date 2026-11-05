# Aplikasi Kriptografi — Projek Akhir Mata Kuliah Kriptografi

Aplikasi desktop kriptografi (PySide6) sesuai rancangan di
`../Rancangan-Projek-Akhir-Kriptografi.md`. Memenuhi 7 kriteria tugas:
login biometrik + dongle, login berkriptografi, super enkripsi teks, enkripsi
file berbeda dari teks, pesan penting terenkripsi di basis data, steganografi
gambar, dan blockchain sederhana.

## Status

Struktur proyek (scaffolding) — **belum ada logika aplikasi**. Implementasi
menyusul per modul sesuai roadmap di §8 rancangan.

## Struktur

```
AplikasiKriptografi/
├── main.py                # titik masuk aplikasi
├── app/
│   ├── core/              # inti kriptografi (murni, tanpa GUI)
│   │   ├── keys.py        # manajemen kunci & KDF (Argon2id, HKDF)
│   │   ├── classic.py     # cipher klasik: Vigenère, Caesar
│   │   ├── modern.py      # cipher modern: LFSR, DES/DEA, HMAC
│   │   ├── super_encrypt.py  # super enkripsi teks (klasik → modern)
│   │   ├── file_crypto.py # enkripsi file ChaCha20-Poly1305
│   │   ├── stego.py       # steganografi gambar (LSB + permutasi)
│   │   └── blockchain.py  # blockchain sederhana (SHA-256 + PoW)
│   ├── security/
│   │   ├── dongle.py      # deteksi & verifikasi dongle USB
│   │   ├── biometric.py   # biometrik wajah webcam (OpenCV)
│   │   └── auth.py        # login kata sandi + sesi token
│   ├── db/
│   │   ├── database.py    # koneksi SQLCipher
│   │   └── schema.sql     # skema basis data
│   ├── ui/                # PySide6
│   │   ├── main_window.py
│   │   ├── login_dialog.py
│   │   ├── text_tab.py
│   │   ├── file_tab.py
│   │   ├── db_tab.py
│   │   ├── image_tab.py
│   │   └── asset_tab.py
│   └── utils/
│       └── paths.py
├── tests/                 # pytest
└── requirements.txt
```

## Menjalankan (nanti, setelah implementasi)

1. Buat venv: `python -m venv .venv` lalu aktifkan.
2. Pasang dependensi: `pip install -r requirements.txt`.
3. Jalankan: `python main.py`.

## Dependensi terencana

PySide6, cryptography, opencv-python, numpy, Pillow, psutil, pytest.
