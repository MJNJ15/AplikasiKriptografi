"""Titik masuk aplikasi — boot dongle → login (GUI) → Jendela Utama.

Penggunaan:
  python main.py                       # jalankan normal (butuh dongle)
  python main.py --provision <drive>   # siapkan flashdisk sebagai dongle
  python main.py --data-dir <dir>      # lokasi data (registry, db)
"""

from __future__ import annotations

import argparse
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
from app.ui.register_dialog import RegisterDialog
from app.ui.theme import apply_theme


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aplikasi Kriptografi")
    parser.add_argument("--provision", metavar="DRIVE", help="siapkan flashdisk sebagai dongle")
    parser.add_argument("--data-dir", type=Path, default=None, help="folder data lokal")
    return parser.parse_args(argv)


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

    # Loop login ⇄ dashboard: logout kembali ke layar login tanpa menutup app.
    while True:
        holder: dict = {"session": None}

        def verify(username: str, password: str) -> tuple[bool, str]:
            try:
                session = auth.login(username, password, info.key)
            except TooManyAttemptsError as exc:
                return False, str(exc)
            except AuthError:
                return False, "username/kata sandi salah"
            holder["session"] = session
            return True, ""

        # Kriteria #1–3: wajah WAJIB pada satu alur login (username+password+wajah).
        # Opsi A: kalau akun belum punya template → wajib enrol sekarang.
        def face_verify(username: str) -> tuple[bool, str]:
            user = store.get_user_by_username(username)
            if not user:
                holder["session"] = None
                return False, "username tidak ditemukan"
            if not user.get("face_template"):
                capture_dlg = CaptureFaceDialog()
                if (
                    capture_dlg.exec() != CaptureFaceDialog.DialogCode.Accepted
                    or not capture_dlg.template_bytes
                ):
                    holder["session"] = None
                    return False, "akun belum punya template wajah — pendaftaran wajah dibatalkan"
                face_login.store_face_template(store, user["id"], db_key, capture_dlg.template_bytes)
                return True, ""
            try:
                template_raw = face_login.decrypt_template(db_key, bytes(user["face_template"]))
            except Exception:
                holder["session"] = None
                return False, "template wajah rusak/tidak valid"
            verify_dlg = VerifyFaceDialog(template_raw)
            if verify_dlg.exec() != VerifyFaceDialog.DialogCode.Accepted:
                holder["session"] = None
                return False, "verifikasi wajah dibatalkan/gagal"
            return True, ""

        # Pendaftaran akun berbasis GUI (menggantikan terminal).
        dlg: Optional[LoginDialog] = None

        def register_handler() -> None:
            nonlocal dlg
            if dlg is None:
                return
            reg_dlg = RegisterDialog()
            if reg_dlg.exec() != RegisterDialog.DialogCode.Accepted:
                return
            username, password = reg_dlg.username, reg_dlg.password
            try:
                auth.register(username, password, info.dongle_id)
            except AuthError as exc:
                QMessageBox.warning(None, "Pendaftaran", str(exc))
                return
            user = store.get_user_by_username(username)
            capture_dlg = CaptureFaceDialog()
            if (
                capture_dlg.exec() == CaptureFaceDialog.DialogCode.Accepted
                and capture_dlg.template_bytes
                and user is not None
            ):
                face_login.store_face_template(store, user["id"], db_key, capture_dlg.template_bytes)
            ok, msg = verify(username, password)
            if not ok:
                QMessageBox.warning(None, "Login", msg)
                return
            QMessageBox.information(
                None,
                "Akun dibuat",
                f"Akun '{username}' berhasil dibuat dan Anda sudah masuk.",
            )
            dlg.accept()

        dlg = LoginDialog(verify=verify, face_verify=face_verify, register_handler=register_handler)

        if dlg.exec() != LoginDialog.DialogCode.Accepted or holder["session"] is None:
            print("Login dibatalkan.")
            db.close()
            return 1

        session = holder["session"]
        window = MainWindow(session.app_key, store, db, session.user_id)

        logged_out = {"flag": False}

        def on_logout() -> None:
            logged_out["flag"] = True
            app.quit()

        window.logout_requested.connect(on_logout)
        window.show()
        app.exec()
        window.close()

        if not logged_out["flag"]:
            break  # jendela utama ditutup → keluar aplikasi

    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
