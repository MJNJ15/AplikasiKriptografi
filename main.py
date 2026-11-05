"""Titik masuk aplikasi — boot dongle → login → Jendela Utama.

Penggunaan:
  python main.py                       # jalankan normal (butuh dongle)
  python main.py --setup               # daftarkan user & template wajah
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
from app.ui.face_dialogs import EnrollFaceDialog, VerifyFaceDialog
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

    print("Membuka jendela webcam untuk merekam wajah…")
    enroll_dlg = EnrollFaceDialog()
    if enroll_dlg.exec() == EnrollFaceDialog.DialogCode.Accepted and enroll_dlg.template_bytes:
        blob = face_login.encrypt_template(db_key, enroll_dlg.template_bytes)
        user = store.get_user_by_username(username)
        store.set_face_template(user["id"], blob)
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

    def face_verify(username: str) -> tuple[bool, str]:
        user = store.get_user_by_username(username)
        if not user or not user.get("face_template"):
            return False, "akun ini belum punya template wajah (jalankan --setup)"
        try:
            template_raw = face_login.decrypt_template(db_key, bytes(user["face_template"]))
        except Exception:
            return False, "template wajah rusak/tidak valid"
        verify_dlg = VerifyFaceDialog(template_raw)
        if verify_dlg.exec() != VerifyFaceDialog.DialogCode.Accepted:
            return False, "verifikasi wajah dibatalkan/gagal"
        # Verifikasi wajah sukses → tetap butuh kata sandi untuk membangun
        # sesi (dua faktor), sesuai rancangan §4.2–4.3.
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
