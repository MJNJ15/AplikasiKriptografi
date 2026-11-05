"""Utilitas path & lokasi berkas (placeholder, belum diimplementasikan)."""

from __future__ import annotations

import pathlib


PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def paths_dir() -> pathlib.Path:
    """Direktori penyimpanan data lokal (config, registry dongle, db)."""
    return pathlib.Path.home() / "AppData" / "Local" / "AplikasiKriptografi"
