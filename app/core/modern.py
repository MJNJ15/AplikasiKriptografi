"""Cipher modern: LFSR, DES/DEA, HMAC — placeholder, belum diimplementasikan.

Dipakai sebagai lapis 2 super enkripsi teks (§4.4): keystream LFSR (XOR)
→ DES/DEA mode CBC → tag HMAC-SHA256.
"""

from __future__ import annotations
