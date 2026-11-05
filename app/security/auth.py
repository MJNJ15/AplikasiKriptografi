"""Login kata sandi + sesi token (§4.3).

Argon2id untuk penyimpanan kata sandi; kunci aplikasi = mix dengan dongle
(§4.7); token sesi acak di memori; batas percobaan (lockout); timeout idle.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Callable, Optional

from ..core import keys
from ..db.database import Database, UserStore

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 30
SESSION_TIMEOUT_SECONDS = 15 * 60


class AuthError(Exception):
    """Kesalahan autentikasi."""


class TooManyAttemptsError(AuthError):
    """Terlalu banyak percobaan gagal — akun dikunci sementara."""


@dataclass
class Session:
    user_id: int
    username: str
    app_key: bytes
    token: bytes
    created_at: float
    last_activity: float


class AuthManager:
    def __init__(
        self,
        store: UserStore,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._store = store
        self._clock = clock
        self._sessions: dict[bytes, Session] = {}
        self._failed: dict[str, list[float]] = {}

    def _remaining_lockout(self, username: str) -> float:
        now = self._clock()
        recent = [t for t in self._failed.get(username, []) if now - t < LOCKOUT_SECONDS]
        self._failed[username] = recent
        if len(recent) >= MAX_ATTEMPTS:
            return max(0.0, LOCKOUT_SECONDS - (now - recent[0]))
        return 0.0

    def register(self, username: str, password: str, dongle_id: str) -> None:
        if self._store.get_user_by_username(username):
            raise AuthError("username sudah terdaftar")
        salt_password = keys.generate_salt()
        hash_password = keys.argon2id_hash(password, salt_password)
        salt_master = keys.generate_salt()
        self._store.insert_user(
            username=username,
            salt_password=salt_password,
            hash_password=hash_password,
            face_template=None,
            salt_master=salt_master,
            dongle_id=dongle_id,
        )

    def login(self, username: str, password: str, dongle_key: bytes) -> Session:
        wait = self._remaining_lockout(username)
        if wait > 0:
            raise TooManyAttemptsError(f"terlalu banyak percobaan; coba lagi dalam {wait:.0f} dtk")

        user = self._store.get_user_by_username(username)
        if user is None:
            raise AuthError("username/kata sandi salah")

        if not keys.verify_password(password, user["salt_password"], user["hash_password"]):
            self._failed.setdefault(username, []).append(self._clock())
            raise AuthError("username/kata sandi salah")

        self._failed.pop(username, None)

        master = keys.derive_master_key(password, user["salt_master"])
        app_key = keys.mix_with_dongle(master, dongle_key)
        token = secrets.token_bytes(32)
        now = self._clock()
        session = Session(
            user_id=user["id"],
            username=username,
            app_key=app_key,
            token=token,
            created_at=now,
            last_activity=now,
        )
        self._sessions[token] = session
        return session

    def get_session(self, token: bytes) -> Optional[Session]:
        session = self._sessions.get(token)
        if session is None:
            return None
        if self._clock() - session.last_activity > SESSION_TIMEOUT_SECONDS:
            del self._sessions[token]
            return None
        session.last_activity = self._clock()
        return session

    def logout(self, token: bytes) -> None:
        self._sessions.pop(token, None)

    def session_count(self) -> int:
        return len(self._sessions)
