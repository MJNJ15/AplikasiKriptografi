"""Uji login & autentikasi (AuthManager + UserStore SQLCipher)."""

from __future__ import annotations

import time

import pytest

from app.core.keys import mix_with_dongle
from app.db.database import Database, UserStore
from app.security.auth import (
    SESSION_TIMEOUT_SECONDS,
    AuthError,
    AuthManager,
    TooManyAttemptsError,
)

DB_KEY = b"K" * 32
DONGLE_KEY = bytes(range(32))


@pytest.fixture
def store(tmp_path) -> UserStore:
    db = Database(str(tmp_path / "auth.db"), DB_KEY)
    return UserStore(db)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_register_and_login_roundtrip(store):
    auth = AuthManager(store)
    auth.register("budi", "rahasia123", "dongle-1")
    s1 = auth.login("budi", "rahasia123", DONGLE_KEY)
    s2 = auth.login("budi", "rahasia123", DONGLE_KEY)
    assert s1.username == "budi"
    assert s1.app_key == s2.app_key
    assert len(s1.app_key) == 32


def test_register_duplicate_rejected(store):
    auth = AuthManager(store)
    auth.register("budi", "rahasia123", "dongle-1")
    with pytest.raises(AuthError):
        auth.register("budi", "lain", "dongle-1")


def test_wrong_password_rejected(store):
    auth = AuthManager(store)
    auth.register("budi", "rahasia123", "dongle-1")
    with pytest.raises(AuthError):
        auth.login("budi", "salah", DONGLE_KEY)


def test_lockout_after_max_attempts(store):
    clock = FakeClock()
    auth = AuthManager(store, clock=clock)
    auth.register("budi", "rahasia123", "dongle-1")
    for _ in range(5):
        with pytest.raises(AuthError):
            auth.login("budi", "salah", DONGLE_KEY)
    with pytest.raises(TooManyAttemptsError):
        auth.login("budi", "rahasia123", DONGLE_KEY)  # benar pun tertahan
    clock.now += 31
    s = auth.login("budi", "rahasia123", DONGLE_KEY)
    assert s.username == "budi"


def test_app_key_depends_on_dongle(store):
    auth = AuthManager(store)
    auth.register("budi", "rahasia123", "dongle-1")
    s1 = auth.login("budi", "rahasia123", b"A" * 32)
    s2 = auth.login("budi", "rahasia123", b"B" * 32)
    assert s1.app_key != s2.app_key


def test_logout_invalidates_session(store):
    auth = AuthManager(store)
    auth.register("budi", "rahasia123", "dongle-1")
    s = auth.login("budi", "rahasia123", DONGLE_KEY)
    assert auth.get_session(s.token) is s
    auth.logout(s.token)
    assert auth.get_session(s.token) is None


def test_session_timeout(store):
    clock = FakeClock()
    auth = AuthManager(store, clock=clock)
    auth.register("budi", "rahasia123", "dongle-1")
    s = auth.login("budi", "rahasia123", DONGLE_KEY)
    clock.now += SESSION_TIMEOUT_SECONDS + 1
    assert auth.get_session(s.token) is None
