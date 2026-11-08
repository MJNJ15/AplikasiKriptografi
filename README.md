# Aplikasi Kriptografi — Projek Akhir Mata Kuliah Kriptografi

Aplikasi desktop kriptografi (PySide6) sesuai rancangan di
`../Rancangan-Projek-Akhir-Kriptografi.md`. Memenuhi 7 kriteria tugas:
login biometrik + dongle, login berkriptografi, super enkripsi teks, enkripsi
file berbeda dari teks, pesan penting terenkripsi di basis data, steganografi
gambar, dan blockchain sederhana.

## Status

Implementasi lengkap (fase 1–5): inti kriptografi, boot & dongle, login
(kata sandi + wajah), UI 5 tab (Teks / File / Basis Data / Gambar / Aset),
semua diuji dengan pytest.

## Struktur

```
AplikasiKriptografi/
├── main.py                # titik masuk: boot dongle → login → jendela utama
├── scripts/
│   └── provision_dongle.py  # siapkan flashdisk sebagai dongle
├── app/
│   ├── core/              # inti kriptografi (murni, tanpa GUI)
│   │   ├── keys.py        # KDF: Argon2id + HKDF, sub-kunci
│   │   ├── classic.py     # Vigenère, Caesar
│   │   ├── modern.py      # DES/DEA-CBC, AES (Rijndael)-CBC
│   │   ├── super_encrypt.py  # super enkripsi teks (klasik → modern)
│   │   ├── file_crypto.py # ChaCha20-Poly1305
│   │   ├── stego.py       # steganografi LSB + permutasi
│   │   └── blockchain.py  # blockchain SHA-256 + PoW + Merkle
│   ├── security/
│   │   ├── dongle.py      # deteksi, verifikasi & provisioning dongle
│   │   ├── boot.py        # orkestrasi boot (DB dikunci kunci dongle)
│   │   ├── auth.py        # login kata sandi + sesi token (lockout)
│   │   ├── biometric.py   # biometrik wajah DNN (YUNet + SFace + CLAHE)
│   │   └── face_login.py  # template wajah terenkripsi (AES-GCM)
│   ├── db/
│   │   ├── database.py    # SQLCipher + UserStore + MessageStore
│   │   └── schema.sql     # skema basis data
│   ├── ui/                # PySide6 (main_window, login_dialog, face_dialogs, camera_widget, 5 tab)
│   └── utils/paths.py
├── tests/                 # pytest (semua suite)
└── requirements.txt
```

## Persiapan & menjalankan

1. **Buat venv & pasang dependensi:**
   ```bash
   python -m venv .venv
   .venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
   ```

2. **Siapkan dongle (flashdisk):** colok flashdisk, lalu:
   ```bash
   .venv/Scripts/python.exe scripts/provision_dongle.py E:
   ```
   (ganti `E:` dengan huruf drive flashdisk). Ini menulis `.dongle.key`
   dan `.dongle.id` ke flashdisk serta mendaftarkannya di
   `%LOCALAPPDATA%/AplikasiKriptografi/DongleRegistry.json`.
   **Jangan format flashdisk itu lagi** setelah didaftarkan.

3. **Daftarkan akun & rekam wajah (sekali):**
   ```bash
   .venv/Scripts/python.exe main.py --setup
   ```
   (webcam akan dipakai bila tersedia; bila tidak, akun tetap dibuat tanpa
   template wajah dan login cukup dengan kata sandi).

4. **Jalankan:**
   ```bash
   .venv/Scripts/python.exe main.py
   ```
   Tanpa dongle, aplikasi menolak hidup.

## Fitur & algoritma (ringkas)

| Kriteria | Fitur | Algoritma |
|----------|-------|-----------|
| 1 | Dongle + biometrik | Flashdisk `.dongle.key` + SHA-256; wajah DNN (YUNet + SFace) |
| 2 | Login berkriptografi | Argon2id, sesi token, lockout |
| 3 | Super enkripsi teks | Vigenère → Caesar → DES/DEA-CBC → AES (Rijndael)-CBC |
| 4 | Enkripsi file | ChaCha20-Poly1305 (berbeda dari teks) |
| 5 | Basis data terenkripsi | SQLCipher + AES-GCM per-rekor (pesan penting) |
| 6 | Steganografi gambar | LSB + permutasi ber-seed, wajib PNG |
| 7 | Blockchain aset | SHA-256 + PoW ringan + akar Merkle |

## Uji

```bash
.venv/Scripts/python.exe -m pytest tests -q
```

## Catatan platform

- Wheel `opencv-contrib` ≥ 5 tidak menyertakan berkas haar cascade; file XML
  diunduh ke `app/security/data/` (sudah di-repo).
- `sqlcipher3` disertakan wheel Windows; `PRAGMA key` memakai passphrase hex.
- Kunci DB SQLCipher diturunkan dari kunci dongle (tersedia sebelum login);
  kolom pesan penting dienkripsi ganda dengan sub-kunci dari sesi password.

## Rollback / checkpoint

Setiap fase ditandai tag git:
`v0.1-scaffold` … `v0.5-fase4` (branch fitur per fase; `main` bersih).

