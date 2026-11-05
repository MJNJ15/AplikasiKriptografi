#!/usr/bin/env python3
"""Alat provisioning dongle — jalankan dari terminal (bukan lewat GUI).

Contoh (Windows):
    .venv/Scripts/python.exe scripts/provision_dongle.py E:

Contoh (Linux/macOS):
    .venv/bin/python scripts/provision_dongle.py /media/user/USB

Ini menulis `.dongle.key` + `.dongle.id` ke flashdisk dan mendaftarkan
digest-nya ke registry lokal. Setelah ini, aplikasi HANYA hidup saat
flashdisk tsb terpasang.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.security.boot import registry_path
from app.security.dongle import DongleError, provision_dongle


def main() -> int:
    parser = argparse.ArgumentParser(description="Siapkan flashdisk sebagai dongle")
    parser.add_argument("drive", help="mountpoint flashdisk, mis. E: atau /media/...")
    parser.add_argument("--registry", default=str(registry_path()), help="lokasi file registry")
    args = parser.parse_args()

    try:
        info = provision_dongle(args.drive, args.registry)
    except DongleError as exc:
        print(f"Provisioning gagal: {exc}", file=sys.stderr)
        return 1

    print("OK — dongle terdaftar.")
    print(f"  Drive   : {info.drive}")
    print(f"  ID      : {info.dongle_id}")
    print(f"  Registry: {args.registry}")
    print("Ingat: jangan format flashdisk ini setelah didaftarkan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
