"""Uji blockchain sederhana (§4.9)."""

from __future__ import annotations

import pytest

from app.core.blockchain import Blockchain


def test_genesis_valid():
    bc = Blockchain(difficulty=4)
    assert len(bc.chain) == 1
    assert bc.chain[0].index == 0
    assert bc.chain[0].previous_hash == "0" * 64
    valid, bad = bc.verify()
    assert valid and bad is None


def test_add_blocks_and_verify():
    bc = Blockchain()
    bc.add_block([{"nama": "Laptop", "hash": "abc123", "pemilik": "Budi"}])
    bc.add_block([{"nama": "Flashdisk", "hash": "def456", "pemilik": "Sari"}])
    assert len(bc.chain) == 3
    assert bc.chain[1].hash.startswith("0000")
    valid, bad = bc.verify()
    assert valid and bad is None


def test_tamper_data_detected():
    bc = Blockchain()
    bc.add_block([{"nama": "Laptop", "hash": "abc123", "pemilik": "Budi"}])
    bc.add_block([{"nama": "Flashdisk", "hash": "def456", "pemilik": "Sari"}])
    bc.chain[1].data[0]["hash"] = "GHANCED"
    valid, bad = bc.verify()
    assert valid is False
    assert bad == 1


def test_tamper_previous_link_detected():
    bc = Blockchain()
    bc.add_block([{"nama": "A", "hash": "1", "pemilik": "X"}])
    bc.chain[1].previous_hash = "0" * 64
    valid, bad = bc.verify()
    assert valid is False
    assert bad == 1


def test_json_roundtrip():
    bc = Blockchain()
    bc.add_block([{"nama": "Aset", "hash": "h1", "pemilik": "P"}])
    restored = Blockchain.from_json(bc.to_json())
    assert len(restored.chain) == len(bc.chain)
    assert restored.chain[1].hash == bc.chain[1].hash
    assert restored.verify() == (True, None)


def test_invalid_difficulty():
    with pytest.raises(ValueError):
        Blockchain(difficulty=0)
