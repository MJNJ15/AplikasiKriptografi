"""Steganografi gambar LSB + permutasi (§4.8).

Bit pesan disisipkan ke LSB (least-significant bit) kanal warna; urutan
slot disusun oleh permutasi dari PRNG yang di-seed kata sandi — tanpa
kunci, lokasi bit tidak diketahui. Prefix 4 byte = panjang pesan (big-endian).

Kerja pada array gambar (BGR/RGB, 3 kanal); penyimpanan PNG lossless
ditangani pemanggil (UI).
"""

from __future__ import annotations

import hashlib

import numpy as np

LENGTH_BYTES = 4
DEFAULT_MAX_LEN = 1024 * 1024


def seed_from_key(key: bytes) -> int:
    """Seed numerik deterministik dari kunci (SHA-256 → 64-bit)."""
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


def capacity(image: np.ndarray) -> int:
    """Jumlah slot bit LSB yang tersedia (W×H×3)."""
    return int(image.shape[0]) * int(image.shape[1]) * 3


def _positions(shape: tuple, key: bytes, nbits: int) -> np.ndarray:
    rng = np.random.default_rng(seed_from_key(key))
    total = shape[0] * shape[1] * 3
    if nbits > total:
        raise ValueError("pesan terlalu besar untuk kapasitas gambar")
    return rng.permutation(total)[:nbits].astype(np.int64)


def _flat_channels(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("gambar harus memiliki 3 kanal (RGB/BGR)")
    return image.reshape(-1, image.shape[2])[:, :3]


def _read_bits(flat: np.ndarray, shape: tuple, key: bytes, nbits: int) -> np.ndarray:
    order = _positions(shape, key, nbits)
    return flat[order // 3, order % 3] & 1


def _write_bits(flat: np.ndarray, shape: tuple, key: bytes, bits: np.ndarray) -> None:
    order = _positions(shape, key, bits.size)
    px, ch = order // 3, order % 3
    flat[px, ch] = (flat[px, ch] & 0xFE) | bits


def embed_message(image: np.ndarray, message: bytes, key: bytes) -> np.ndarray:
    """Sisipkan pesan; kembalikan salinan gambar stego."""
    img = image.copy()
    payload = len(message).to_bytes(LENGTH_BYTES, "big") + message
    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
    if bits.size > capacity(img):
        raise ValueError("pesan terlalu besar untuk kapasitas gambar")
    flat = _flat_channels(img)
    _write_bits(flat, img.shape, key, bits)
    return flat.reshape(img.shape)


def extract_message(
    image: np.ndarray, key: bytes, max_len: int = DEFAULT_MAX_LEN
) -> bytes:
    """Ekstrak pesan. Kunci salah / bukan stego → ValueError."""
    flat = _flat_channels(image)
    length_bits = _read_bits(flat, image.shape, key, LENGTH_BYTES * 8)
    length = int.from_bytes(np.packbits(length_bits).tobytes(), "big")
    if length > max_len:
        raise ValueError("panjang pesan melebihi batas maksimum")
    total_bits = (LENGTH_BYTES + length) * 8
    if total_bits > capacity(image):
        raise ValueError("pesan tidak muat — kunci salah atau gambar bukan stego")
    bits = _read_bits(flat, image.shape, key, total_bits)
    payload = np.packbits(bits).tobytes()
    if int.from_bytes(payload[:LENGTH_BYTES], "big") != length:
        raise ValueError("kunci salah atau gambar bukan stego")
    return payload[LENGTH_BYTES : LENGTH_BYTES + length]
