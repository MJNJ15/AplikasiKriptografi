"""Uji manajemen kunci & KDF."""

from __future__ import annotations

import pytest

from app.core.keys import (
    derive_master_key,
    derive_subkey,
    generate_salt,
    mix_with_dongle,
    verify_password,
)

PASSWORD = "kata-sandi-uji"


def test_master_key_requires_salt():
    a = derive_master_key(PASSWORD, generate_salt())
    b = derive_master_key(PASSWORD, generate_salt())
    assert len(a) == 32
    assert a != b


def test_verify_password():
    salt = generate_salt()
    h = derive_master_key(PASSWORD, salt)
    assert verify_password(PASSWORD, salt, h) is True
    assert verify_password("salah", salt, h) is False


def test_mix_with_dongle_deterministic():
    master = derive_master_key(PASSWORD, generate_salt())
    dongle = bytes(range(32))
    a = mix_with_dongle(master, dongle)
    b = mix_with_dongle(master, dongle)
    assert a == b
    assert a != mix_with_dongle(master, bytes(reversed(dongle)))


def test_subkeys_distinct():
    app_key = derive_master_key(PASSWORD, generate_salt())
    des = derive_subkey(app_key, "des", length=8)
    mac = derive_subkey(app_key, "mac")
    classic = derive_subkey(app_key, "classic", length=16)
    assert len(des) == 8 and len(mac) == 32 and len(classic) == 16
    assert len({des, mac, classic}) == 3


def test_unknown_subkey_rejected():
    app_key = derive_master_key(PASSWORD, generate_salt())
    with pytest.raises(ValueError):
        derive_subkey(app_key, "tidak-ada")
