"""Titik masuk aplikasi — boot dongle → login → Jendela Utama.

Penggunaan:
  python main.py                       # jalankan normal (butuh dongle)
  python main.py --setup               # daftarkan user baru
  python main.py --provision <drive>   # siapkan flashdisk sebagai dongle
  python main.py --data-dir <dir>      # lokasi data (registry, db)
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox

from app.db.database import UserStore
from app.security import face_login
from app.security.auth import AuthError, AuthManager, TooManyAttemptsError
from app.security.boot import (
    boot_with_dongle,
    db_key_from_dongle,
    open_boot_database,
    registry_path,
)
from app.security.dongle import DongleError, provision_dongle
from app.ui.face_dialogs import CaptureFaceDialog, VerifyFaceDialog
from app.ui.login_dialog import LoginDialog
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aplikasi Kriptografi")
    parser.add_argument("--setup", action="store_true", help="daftarkan akun baru")
    parser.add_argument("--provision", metavar="DRIVE", help="siapkan flashdisk sebagai dongle")
    parser.add_argument("--data-dir", type=Path, default=None, help="folder data lokal")
    return parser.parse_args(argv)


def _prompt_register(auth: AuthManager, store: UserStore, dongle_id: str, db_key: bytes) -> str:
    print("=== Pendaftaran akun baru ===")
    while True:
        username = input("Username: ").strip()
        if username and store.get_user_by_username(username) is None:
            break
        print("Username tidak valid / sudah dipakai.")
    while True:
        password = getpass.getpass("Password baru: ")
        confirm = getpass.getpass("Ulangi password: ")
        if password and password == confirm:
            break
        print("Password kosong atau tidak sama.")
    auth.register(username, password, dongle_id)

    # Kriteria #1: pop-up webcam preview + tombol "Simpan Foto"
    print("Membuka jendela webcam untuk menyimpan foto wajah…")
    capture_dlg = CaptureFaceDialog()
    if capture_dlg.exec() == CaptureFaceDialog.DialogCode.Accepted and capture_dlg.template_bytes:
        user = store.get_user_by_username(username)
        if user is not None:
            face_login.store_face_template(store, user["id"], db_key, capture_dlg.template_bytes)
            print("Template wajah tersimpan (terenkripsi).")
    else:
        print("Perekaman dibatalkan/kamera tidak tersedia — akun tanpa biometrik.")
    return username


def run(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    if args.provision:
        try:
            info = provision_dongle(args.provision, registry_path(args.data_dir))
        except DongleError as exc:
            print(f"Provisioning gagal: {exc}", file=sys.stderr)
            return 1
        print("OK — dongle terdaftar.")
        print(f"  Drive   : {info.drive}")
        print(f"  ID      : {info.dongle_id}")
        print(f"  Registry: {registry_path(args.data_dir)}")
        return 0

    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app, dark=True)  # dark mode default

    try:
        info = boot_with_dongle(args.data_dir)
    except DongleError as exc:
        print(f"Boot ditolak: {exc}", file=sys.stderr)
        QMessageBox.critical(None, "Dongle", f"Aplikasi tidak dapat hidup:\n{exc}")
        return 1

    db = open_boot_database(info, args.data_dir)
    store = UserStore(db)
    auth = AuthManager(store)
    db_key = db_key_from_dongle(info.key)

    usernames = [u["username"] for u in store.list_users()]
    if not usernames or args.setup:
        username = _prompt_register(auth, store, info.dongle_id, db_key)
        usernames = [username]

    holder: dict = {"session": None, "dlg": None}

    def verify(username: str, password: str) -> tuple[bool, str]:
        try:
            session = auth.login(username, password, info.key)
        except TooManyAttemptsError as exc:
            return False, str(exc)
        except AuthError:
            return False, "username/kata sandi salah"
        holder["session"] = session
        return True, ""

    # Kriteria #2 & #3: pop-up webcam preview + kotak + persentase kemiripan
    def face_verify(username: str) -> tuple[bool, str]:
        try:
            template_raw = face_login.load_face_template(store, username, db_key)
        except ValueError as exc:
            return False, str(exc)
        verify_dlg = VerifyFaceDialog(template_raw)
        if verify_dlg.exec() != VerifyFaceDialog.DialogCode.Accepted:
            return False, "verifikasi wajah dibatalkan/gagal"
        # Wajah cocok → tetap butuh kata sandi untuk membangun sesi (dua faktor).
        dlg = holder["dlg"]
        return verify(username, dlg.password_edit.text())

    dlg = LoginDialog(verify=verify, face_verify=face_verify, initial_username=usernames[0])
    holder["dlg"] = dlg

    if dlg.exec() != LoginDialog.DialogCode.Accepted or holder["session"] is None:
        print("Login dibatalkan.")
        db.close()
        return 1

    session = holder["session"]
    window = MainWindow(session.app_key, store, db, session.user_id)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
