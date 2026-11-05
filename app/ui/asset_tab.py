"""Tab Aset: blockchain sederhana (tambah & verifikasi rantai) — §4.9.

Menyimpan riwayat penambahan aset dalam rantai blok; verifikasi keutuhan
mendeteksi perubahan data (tamper-evident).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..core.blockchain import Blockchain


class AssetTab(QWidget):
    def __init__(self, difficulty: int = 4, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.blockchain = Blockchain(difficulty=difficulty)

        self.name_edit = self._line_edit("Nama aset")
        self.hash_edit = self._line_edit("Hash aset (mis. SHA-256)")
        self.owner_edit = self._line_edit("Pemilik")

        self.add_btn = QPushButton("Tambah Aset")
        self.verify_btn = QPushButton("Verifikasi Rantai")
        self.save_btn = QPushButton("Simpan Rantai…")
        self.load_btn = QPushButton("Muat Rantai…")
        self.status_label = QLabel("Siap.")

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Blok", "Waktu", "Data", "Hash (12)"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.add_btn.clicked.connect(self._on_add)
        self.verify_btn.clicked.connect(self._on_verify)
        self.save_btn.clicked.connect(self._on_save)
        self.load_btn.clicked.connect(self._on_load)

        actions = QHBoxLayout()
        actions.addWidget(self.add_btn)
        actions.addWidget(self.verify_btn)
        actions.addWidget(self.save_btn)
        actions.addWidget(self.load_btn)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.name_edit)
        layout.addWidget(self.hash_edit)
        layout.addWidget(self.owner_edit)
        layout.addLayout(actions)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)
        self.refresh()

    @staticmethod
    def _line_edit(placeholder: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        return edit

    def refresh(self) -> None:
        self.table.setRowCount(len(self.blockchain.chain))
        for i, block in enumerate(self.blockchain.chain):
            self.table.setItem(i, 0, QTableWidgetItem(str(block.index)))
            self.table.setItem(i, 1, QTableWidgetItem(f"{block.timestamp:.0f}"))
            self.table.setItem(i, 2, QTableWidgetItem(str(len(block.data))))
            self.table.setItem(i, 3, QTableWidgetItem(block.hash[:12]))

    def _on_add(self) -> None:
        nama = self.name_edit.text().strip()
        hash_aset = self.hash_edit.text().strip()
        pemilik = self.owner_edit.text().strip()
        if not nama or not hash_aset:
            self.status_label.setText("Nama dan hash aset wajib diisi.")
            return
        block = self.blockchain.add_block([{"nama": nama, "hash": hash_aset, "pemilik": pemilik}])
        self.name_edit.clear()
        self.hash_edit.clear()
        self.owner_edit.clear()
        self.refresh()
        self.status_label.setText(f"Aset dicatat di blok #{block.index}.")

    def _on_verify(self) -> None:
        valid, index = self.blockchain.verify()
        if valid:
            self.status_label.setText(f"Rantai VALID ({len(self.blockchain.chain)} blok).")
        else:
            self.status_label.setText(f"Rantai RUSAK — masalah pada blok #{index}.")
            QMessageBox.warning(self, "Verifikasi", f"Rantai dirusak pada blok #{index}.")

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Simpan rantai", "chain.json", "JSON (*.json)")
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self.blockchain.to_json(), indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Simpan gagal", str(exc))
            return
        self.status_label.setText(f"Rantai tersimpan: {Path(path).name}")

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Muat rantai", "", "JSON (*.json)")
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            self.blockchain = Blockchain.from_json(payload)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Muat gagal", str(exc))
            return
        self.refresh()
        self.status_label.setText(f"Rantai dimuat: {Path(path).name}")
