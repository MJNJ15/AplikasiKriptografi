"""Tab Aset: blockchain sederhana (tambah & verifikasi rantai) — §4.9.

Menyimpan riwayat penambahan aset dalam rantai blok; verifikasi keutuhan
mendeteksi perubahan data (tamper-evident). Penambahan blok (PoW) diberi
state "menambang": tombol nonaktif + pulse agar pengguna tahu proses berjalan.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication,
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
from .animations import pulse
from .widgets import StatusLabel


def _format_block_time(timestamp: float) -> str:
    try:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    except (ValueError, OSError, OverflowError):
        return f"{timestamp:.0f}"


class AssetTab(QWidget):
    def __init__(self, difficulty: int = 4, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.blockchain = Blockchain(difficulty=difficulty)
        self._mining = False

        self.name_edit = self._line_edit("Nama aset")
        self.id_edit = self._line_edit("ID Aset")
        self.owner_edit = self._line_edit("Pemilik")

        self.add_btn = QPushButton("Tambah Aset")
        self.add_btn.setObjectName("accentBtn")
        self.add_btn.setToolTip("Catat aset baru ke rantai (PoW ringan)")
        self.verify_btn = QPushButton("Verifikasi Rantai")
        self.save_btn = QPushButton("Simpan Rantai…")
        self.load_btn = QPushButton("Muat Rantai…")
        self.status_label = StatusLabel("Siap.")

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Blok", "Waktu", "Data", "Hash (12)"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

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
        layout.addWidget(QLabel("Nama aset:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("ID Aset:"))
        layout.addWidget(self.id_edit)
        layout.addWidget(QLabel("Pemilik:"))
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
            self.table.setItem(i, 1, QTableWidgetItem(_format_block_time(block.timestamp)))
            self.table.setItem(i, 2, QTableWidgetItem(str(len(block.data))))
            self.table.setItem(i, 3, QTableWidgetItem(block.hash[:12]))

    def _on_add(self) -> None:
        if self._mining:
            return
        nama = self.name_edit.text().strip()
        id_aset = self.id_edit.text().strip()
        pemilik = self.owner_edit.text().strip()
        if not nama or not id_aset:
            self.status_label.error("Nama dan ID aset wajib diisi.")
            return

        self._mining = True
        self.add_btn.setEnabled(False)
        self.status_label.set_state("info", "Menambang…")
        pulse(self.status_label, ms=900, low=0.4)
        QApplication.processEvents()

        try:
            block = self.blockchain.add_block(
                [{"nama": nama, "id": id_aset, "pemilik": pemilik}]
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Gagal menambang", str(exc))
            self.status_label.error("Gagal menambang blok.")
            block = None
        finally:
            self._mining = False
            self.add_btn.setEnabled(True)

        if block is None:
            return
        self.name_edit.clear()
        self.id_edit.clear()
        self.owner_edit.clear()
        self.refresh()
        self.status_label.success(f"Aset dicatat di blok #{block.index}.")

    def _on_verify(self) -> None:
        valid, index = self.blockchain.verify()
        if valid:
            self.status_label.success(f"Rantai VALID ({len(self.blockchain.chain)} blok).")
        else:
            self.status_label.error(f"Rantai RUSAK — masalah pada blok #{index}.")
            QMessageBox.warning(self, "Verifikasi", f"Rantai dirusak pada blok #{index}.")

    def _on_save(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Simpan rantai", "chain.json", "JSON (*.json)")
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(self.blockchain.to_json(), indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Simpan gagal", str(exc))
            self.status_label.error("Gagal menyimpan rantai.")
            return
        self.status_label.success(f"Rantai tersimpan: {Path(path).name}")

    def _on_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Muat rantai", "", "JSON (*.json)")
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            self.blockchain = Blockchain.from_json(payload)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Muat gagal", str(exc))
            self.status_label.error("Gagal memuat rantai.")
            return
        self.refresh()
        self.status_label.success(f"Rantai dimuat: {Path(path).name}")
