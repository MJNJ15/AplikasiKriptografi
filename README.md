# Aplikasi Kriptografi — Projek Akhir Mata Kuliah Kriptografi

Aplikasi desktop kriptografi (**PySide6**) yang memadukan **tujuh kriteria**
dalam satu sistem: dongle fisik, login biometrik wajah, login berkriptografi,
super enkripsi teks, enkripsi file, basis data terenkripsi, steganografi
gambar, dan blockchain sederhana.

Aplikasi dibangun dengan prinsip *keamanan berlapis* (defense-in-depth):
kunci-kunci saling dirantai dari dongle fisik + kata sandi, dan setiap fitur
memakai turunan kunci tersendiri (HKDF) sehingga pembocoran satu fitur tidak
merembet ke fitur lain.

---

## Daftar Isi

1. [Alur Aplikasi dari Awal sampai Akhir](#alur-aplikasi-dari-awal-sampai-akhir)
2. [Struktur Folder](#struktur-folder)
3. [Persiapan & Menjalankan](#persiapan--menjalankan)
4. [Fitur & Algoritma — Langkah demi Langkah](#fitur--algoritma--langkah-demi-langkah)
5. [Catatan Desain & Kejujuran Kriptografi](#catatan-desain--kejujuran-kriptografi)

---

## Alur Aplikasi dari Awal sampai Akhir

```
provision dongle (sekali)
      │
      ▼
  Boot main.py ──► temukan & verifikasi dongle USB
      │              (ID + SHA-256 vs registry lokal)
      │
      ▼
  Buka basis data SQLCipher (kunci diturunkan dari dongle)
      │
      ▼
  Login 3 faktor dalam satu alur:
      username + kata sandi (Argon2id) ──► wajah (DNN) ──► sesi
      │
      ▼
  Dashboard — 5 tab: Teks · File · Basis Data · Gambar · Aset
      │
      ▼
  Logout → kembali ke layar login | tutup jendela → keluar
```

### 1. Provisioning dongle (dilakukan sekali per flashdisk)

`scripts/provision_dongle.py <drive>` mempersiapkan flashdisk sebagai
dongle:

1. Membuat **kunci acak 32 byte** (`.dongle.key`) dan **UUID** identitas
   (`.dongle.id`) di flashdisk.
2. Mendaftarkan digest **SHA-256(kunci)** di registry lokal
   (`%LOCALAPPDATA%/AplikasiKriptografi/DongleRegistry.json`).
3. Kunci disimpan **hanya di flashdisk** — tidak pernah di komputer;
   registry hanya menyimpan digest (bukan kunci).

> ⚠️ Jangan format flashdisk setelah didaftarkan — kunci akan hilang dan
> data yang terenkripsi dengannya tidak dapat dibuka lagi.

### 2. Boot: verifikasi dongle

1. `main.py` memanggil `boot_with_dongle()`.
2. Drive removable ditemukan via **psutil** (tanpa hardcode huruf drive).
3. Untuk tiap drive, aplikasi mencari `.dongle.key` + `.dongle.id`.
4. ID dicocokkan dengan registry, lalu digest `SHA-256(key)` dibandingkan
   secara *constant-time* (`hmac.compare_digest`).
5. Gagal verifikasi → aplikasi menolak hidup (tampil pesan kritis).

### 3. Buka basis data terenkripsi (SQLCipher)

- Kunci database **diturunkan dari kunci dongle**:
  `db_key = SHA-256(dongle_key ‖ "app-db-key-v1")`.
- Karena berasal dari dongle, database sudah bisa dibuka **sebelum login**
  (kunci tidak bergantung kata sandi).
- Seluruh file `.db` dienkripsi SQLCipher (`PRAGMA key` saat koneksi).

### 4. Login 3 faktor (satu alur)

Alur login di `LoginDialog` menggabungkan **kata sandi + wajah** dalam satu
tombol Login:

1. **Kata sandi** — hash `Argon2id` diverifikasi:
   - Parameter OWASP: memori 64 MiB, iterasi 3, paralelisme 4, salt acak
     16 byte per pengguna.
   - Gagal 5× berturut-turut → **lockout 30 detik**.
2. **Wajah** (wajib) — template DNN dienkripsi **AES-GCM** dengan kunci
   database; akun tanpa template dipaksa merekam wajah saat login.
3. **Sesi** — setelah lolos, `master_key = Argon2id(password, salt_master)`
   dicampur dengan kunci dongle:
   ```
   app_key = HKDF-SHA256(dongle.key ‖ master_key, info="app-master")
   ```
   - Token sesi acak (32 byte) disimpan di memori; timeout idle 15 menit.

Setiap fitur memakai **sub-kunci** turunan `app_key` dengan `info` berbeda:

| Fitur | Info HKDF |
|-------|-----------|
| Teks klasik (Vigenère/Caesar) | `text-classic` |
| DES super enkripsi | `text-des` |
| AES Rijndael | `text-aes` |
| File ChaCha20 | `file-chacha` |
| Basis data (pesan penting) | `db-sqlcipher` |
| Steganografi gambar | `img-stego` |
| Blockchain aset | `asset-chain` |

### 5. Dashboard

Lima tab dengan fungsi:

| Tab | Fungsi |
|-----|--------|
| **Teks** | Super enkripsi teks (klasik → modern) |
| **File** | Enkripsi/dekripsi file ChaCha20-Poly1305 (`.enc`) |
| **Basis Data** | Simpan/tampilkan pesan; pesan penting AES-GCM per-rekor |
| **Gambar** | Steganografi LSB (sisip & ekstrak pesan pada PNG) |
| **Aset** | Blockchain sederhana — catat & verifikasi rantai aset |

### 6. Keluar

- **Logout** → buang sesi, kembali ke layar login (loop di `main.py`).
- Menutup jendela utama → keluar dari aplikasi.

---

## Struktur Folder

```
AplikasiKriptografi/
├── main.py                # titik masuk: boot dongle → login → jendela utama
├── scripts/
│   └── provision_dongle.py  # siapkan flashdisk sebagai dongle
├── app/
│   ├── core/              # inti kriptografi (murni, tanpa GUI)
│   │   ├── keys.py        # Argon2id + HKDF, turunan sub-kunci
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
│   ├── ui/                # PySide6
│   │   ├── main_window.py # jendela utama (header + 5 tab)
│   │   ├── login_dialog.py / register_dialog.py
│   │   ├── face_dialogs.py / camera_widget.py
│   │   ├── text_tab.py / file_tab.py / db_tab.py
│   │   ├── image_tab.py / asset_tab.py
│   │   ├── theme.py       # tema 60/30/10 (teal/slate/oranye)
│   │   ├── animations.py  # fade-in, cross-fade tab, pulse
│   │   ├── widgets.py     # StatusLabel semantik (ok/error/info)
│   │   ├── icons.py       # ikon SVG inline (dapat diwarnai tema)
│   │   └── assets/        # gambar Unsplash, ikon, font Plus Jakarta Sans
│   └── utils/paths.py     # lokasi folder data lokal
└── requirements.txt
```

---

## Persiapan & Menjalankan

1. **Buat venv & pasang dependensi:**
   ```bash
   python -m venv .venv
   .venv/Scripts/python.exe -m pip install -r requirements.txt   # Windows
   ```

2. **Siapkan dongle (flashdisk):** colok flashdisk, lalu:
   ```bash
   .venv/Scripts/python.exe scripts/provision_dongle.py E:
   ```
   (ganti `E:` dengan huruf drive flashdisk).

3. **Jalankan aplikasi:**
   ```bash
   .venv/Scripts/python.exe main.py
   ```
   - Di layar login klik **"Buat Akun Baru"** → isi username & kata sandi
     → rekam wajah (webcam) → akun dibuat dan langsung masuk.
   - Login berikutnya = username + kata sandi + wajah (wajah wajib).

Argument tambahan:

| Argumen | Fungsi |
|---------|--------|
| `--provision <drive>` | Siapkan flashdisk sebagai dongle |
| `--data-dir <dir>` | Pindahkan lokasi data (registry, db) |

---

## Fitur & Algoritma — Langkah demi Langkah

### Kriteria 1 — Dongle + Biometrik

**Dongle fisik (SHA-256 + registry)**

1. Provisioning menulis kunci acak 32 byte `.dongle.key` + UUID
   `.dongle.id` ke flashdisk.
2. Registry lokal menyimpan `digest = SHA-256(key)`.
3. Saat boot: aplikasi membaca kunci dari flashdisk, menghitung digest,
   dan membandingkannya dengan registry secara constant-time.
4. Opsional: strengthening **challenge-response HMAC-SHA256** tersedia di
   `dongle.hmac_challenge_response`.

**Biometrik wajah (DNN YUNet + SFace + CLAHE)**

1. **Deteksi wajah** — `FaceDetectorYN` (YUNet, ONNX): menemukan kotak
   pembatas (threshold skor 0.8).
2. **Normalisasi cahaya** — setiap crop wajah diproses **CLAHE**
   (Contrast Limited Adaptive Histogram Equalization) pada saluran Value
   HSV, agar tahan perubahan kecerahan.
3. **Ekstraksi ciri** — `FaceRecognizerSF` (SFace, ONNX) menghasilkan
   **embedding 128 dimensi**.
4. **Pencocokan** — kosinus similarity antara embedding tersimpan vs
   live; ≥ **0.45** dianggap cocok, ditampilkan sebagai persentase.
5. **Penyimpanan** — template dienkripsi **AES-GCM** dengan kunci database
   sebelum disimpan di kolom `users.face_template`.

### Kriteria 2 — Login Berkriptografi

**Pendaftaran**

1. Generate `salt_password` dan `salt_master` (16 byte acak).
2. Simpan `hash_password = Argon2id(password, salt_password)`.
3. Simpan baris pengguna: username unik, salt, hash, salt_master,
   `dongle_id`.

**Login**

1. Periksa lockout (5 gagal → tunggu 30 detik).
2. Verifikasi `Argon2id` (constant-time, `verify()`).
3. `master_key = Argon2id(password, salt_master)`.
4. `app_key = HKDF-SHA256(dongle.key ‖ master_key, info="app-master")`.
5. Buat token sesi acak; sesi timeout idle 15 menit.
6. Sub-kunci fitur diturunkan via HKDF dengan `info` berbeda (tabel di atas).

### Kriteria 3 — Super Enkripsi Teks

Empat lapis, klasik → modern — urutan **enkripsi**:

```
plaintext
   │ 1. Vigenère(kunci)        — polialfabetik (A–Z/a–z)
   ▼
   │ 2. Caesar(kunci)          — shift = jumlah byte kunci mod 26
   ▼
   │ 3. DES/DEA-CBC(kunci)     — kunci 8 byte + IV acak 8 byte + PKCS7
   ▼
   │ 4. AES Rijndael-CBC       — kunci 16/24/32 byte + IV acak 16 byte
   ▼
Base64( iv_des(8) ‖ iv_aes(16) ‖ ciphertext )
```

- **Vigenère**: tiap huruf digeser oleh kunci yang berulang
  (`Cᵢ = (Pᵢ + Kᵢ mod 26)`); kunci diambil mod 26; non-huruf diteruskan.
  Contoh vektor uji: `ATTACKATDAWN` + kunci `LEMON` → `LXFOPVEFRNHR`.
- **Caesar**: shift tunggal = jumlah nilai byte kunci mod 26.
- **DES/DEA-CBC**: kunci dinormalisasi ke 8 byte (SHA-256 bila bukan 8),
  bit paritas ganjil dikoreksi, padding PKCS7, IV acak 8 byte.
- **AES (Rijndael)-CBC**: kunci dinormalisasi ke 16/24/32 byte
  (SHA-256 → 32 byte untuk lain-lain), padding PKCS7, IV acak 16 byte.

Dekripsi = urutan **terbalik**: AES → DES → Caesar → Vigenère, memakai
IV yang disimpan di awal blob.

### Kriteria 4 — Enkripsi File

**ChaCha20-Poly1305** — sengaja berbeda dari teks (bukan AES):

```
file asli → ChaCha20Poly1305(key32, nonce 12 byte acak)
          → nonce(12) ‖ ciphertext ‖ tag(16)   → disimpan .enc
```

- Kunci = sub-kunci `file-chacha` (32 byte).
- `nonce` acak per operasi — menyisipkan nonce di depan memungkinkan
  dekripsi tanpa menyimpan status.
- **Tag autentikasi Poly1305 (16 byte)** — kunci/berkas salah atau rusak
  ditolak (`InvalidTag`).
- Dekripsi = parse nonce → verifikasi tag → kembalikan bytes asli.

### Kriteria 5 — Basis Data Terenkripsi

1. Seluruh file `.db` dienkripsi **SQLCipher** (`PRAGMA key` saat koneksi;
   kunci = turunan dongle).
2. Pesan **penting** (checkbox) menambah satu lapis: isi dienkripsi
   **AES-GCM** per-rekor memakai sub-kunci `db-sqlcipher` → kolom `isi`
   bertipe BLOB.
3. Saat melihat pesan penting, aplikasi menampilkan **ciphertext Base64**
   secara default; tombol **"Tampilkan Isi Asli"** baru mendekripsi
   (sesuai prinsip *least privilege*).
4. Pesan biasa disimpan sebagai teks polos di dalam DB SQLCipher.

### Kriteria 6 — Steganografi Gambar

**LSB + permutasi ber-seed** (wajib PNG lossless):

```
Sisip:
  1. payload = panjang(4 byte big-endian) ‖ pesan
  2. bit pesan = unpackbits(payload)
  3. Posisi slot bit = permutasi PRNG(seed = SHA-256(password) → 64-bit)
  4. LSB tiap kanal (BGR) diganti: p & 0xFE | bit

Ekstrak:
  1. baca 32 bit pertama pada posisi terurut → panjang
  2. baca bit pesan, packbits → bytes
  3. validasi ulang prefix panjang (tolak kunci salah / gambar bukan stego)
```

- Kapasitas = `W × H × 3` bit (satu bit per kanal per piksel).
- Tanpa kata sandi yang sama, lokasi bit tidak dapat diketahui (permutasi).
- Perubahan LSB praktis tak terlihat oleh mata.

### Kriteria 7 — Blockchain Aset

Struktur blok: `index, timestamp, data, previous_hash, merkle_root,
nonce, hash`.

```
Tambah blok:
  1. data = daftar aset [{nama, id, pemilik}]
  2. merkle_root(data) = akar pohon Merkle (SHA-256; duplikasi daun ganjil)
  3. header = index|timestamp|data|previous_hash|merkle_root|nonce
  4. PoW: increment nonce sampai SHA-256(header) diawali difficulty nol
     (default 4 → "0000…")
  5. hash blok = SHA-256(header akhir); tautkan ke blok sebelumnya
```

**Verifikasi rantai** memeriksa 4 hal pada tiap blok:

1. hash diawali target nol (PoW sah);
2. `compute_hash()` = `hash` tersimpan (data tidak diubah);
3. `merkle_root` cocok dengan data (integritas aset);
4. `previous_hash` menyambung ke hash blok sebelumnya (rantai utuh).

Rantai dapat disimpan/dimuat sebagai JSON (`Simpan Rantai…` / `Muat
Rantai…`).

---

## Catatan Desain & Kejujuran Kriptografi

- **DES 56-bit efektif** sudah usang secara kriptografi; di sini dipakai
  sebagai materi tugas dan **ditutup AES** sebagai lapisan terluar.
- Tab teks **tanpa HMAC** — integritas bukan fokus; kebenaran kunci
  terlihat dari keterbacaan hasil dekripsi.
- **Steganografi bukan pengganti enkripsi** — ia menyembunyikan keberadaan,
  bukan isi; kombinasikan dengan enkripsi bila diperlukan.
- UI memakai tema **60/30/10** (teal/slate/oranye, referensi
  ui-ux-pro-max), tipografi Plus Jakarta Sans, animasi fade/cross-fade,
  dan status semantik (hijau sukses / merah error).
