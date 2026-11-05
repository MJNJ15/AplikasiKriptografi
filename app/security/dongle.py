"""Deteksi & verifikasi dongle USB — placeholder, belum diimplementasikan.

§4.1: cari `.dongle.key` di drive removable (psutil.disk_partitions),
verifikasi ID + SHA-256(key) terhadap registry lokal, lalu challenge-response
HMAC-SHA256. Jangan hardcode huruf drive.
"""

from __future__ import annotations
