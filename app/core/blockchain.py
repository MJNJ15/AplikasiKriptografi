"""Blockchain sederhana untuk aset (§4.9).

Rantai blok SHA-256 + proof-of-work ringan (hash diawali `difficulty` nol)
+ akar Merkle + verifikasi keutuhan. Struktur blok:
    index, timestamp, data (daftar aset), previous_hash, merkle_root,
    nonce, hash.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Optional

DIFFICULTY_DEFAULT = 4
GENESIS_PREV = "0" * 64


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def serialize_data(data: list) -> bytes:
    """Serialisasi data stabil (urutan kunci diurutkan)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def merkle_root(data: list) -> str:
    """Akar pohon Merkle dari daftar aset; kosong → hash dari byte kosong."""
    if not data:
        return sha256_hex(b"")
    leaves = [sha256_hex(serialize_data([item])) for item in data]
    while len(leaves) > 1:
        if len(leaves) % 2:
            leaves.append(leaves[-1])
        leaves = [
            sha256_hex(leaves[i].encode("utf-8") + leaves[i + 1].encode("utf-8"))
            for i in range(0, len(leaves), 2)
        ]
    return leaves[0]


@dataclass
class Block:
    index: int
    timestamp: float
    data: list
    previous_hash: str
    merkle_root: str
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        header = (
            f"{self.index}|{self.timestamp}|"
            f"{serialize_data(self.data).decode('utf-8')}|"
            f"{self.previous_hash}|{self.merkle_root}|{self.nonce}"
        )
        return sha256_hex(header.encode("utf-8"))


class Blockchain:
    def __init__(self, difficulty: int = DIFFICULTY_DEFAULT) -> None:
        if difficulty < 1:
            raise ValueError("difficulty minimal 1")
        self.difficulty = difficulty
        self.chain: list[Block] = [self._mine(self._genesis_block())]

    @staticmethod
    def _genesis_block() -> Block:
        return Block(
            index=0,
            timestamp=time.time(),
            data=[],
            previous_hash=GENESIS_PREV,
            merkle_root=merkle_root([]),
        )

    def _target(self) -> str:
        return "0" * self.difficulty

    def _mine(self, block: Block) -> Block:
        target = self._target()
        while not block.compute_hash().startswith(target):
            block.nonce += 1
        block.hash = block.compute_hash()
        return block

    def add_block(self, data: list) -> Block:
        prev = self.chain[-1]
        block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            data=data,
            previous_hash=prev.hash,
            merkle_root=merkle_root(data),
        )
        mined = self._mine(block)
        self.chain.append(mined)
        return mined

    def verify(self) -> tuple[bool, Optional[int]]:
        """Kembalikan (valid, index_blok_bermasalah atau None)."""
        target = self._target()
        for i, block in enumerate(self.chain):
            if not block.hash.startswith(target):
                return False, i
            if block.compute_hash() != block.hash:
                return False, i
            if block.merkle_root != merkle_root(block.data):
                return False, i
            if i > 0 and block.previous_hash != self.chain[i - 1].hash:
                return False, i
        return True, None

    def to_json(self) -> dict:
        return {"difficulty": self.difficulty, "chain": [asdict(b) for b in self.chain]}

    @classmethod
    def from_json(cls, payload: dict) -> "Blockchain":
        bc = cls(difficulty=payload["difficulty"])
        bc.chain = [Block(**raw) for raw in payload["chain"]]
        return bc
