"""Tab Basis Data: simpan/tampilkan pesan (penting vs biasa) — §4.6.

Dipisah menjadi dua sub-tab: "Tambah Pesan" dan "Lihat Pesan".
Menggunakan `MessageStore` (SQLCipher + AES-GCM per-rekor utk penting).
"""

from __future__ import annotations

import base64
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..db.database import MessageStore


class AddMessagePanel(QWidget):
    """Sub-tab Tambah Pesan: form judul + isi + penting."""

    saved = Signal()

    def __init__(self, store: MessageStore, owner_id: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = store
        self._owner_id = owner_id

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("contoh: Catatan rahasia…")
        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("Isi pesan…")
        self.important_check = QCheckBox("Pesan penting (enkripsi tambahan)")
        self.save_btn = QPushButton("Simpan Pesan")
        self.status_label = QLabel("Siap.")

        self.save_btn.clicked.connect(self._on_save)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.save_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Judul Pesan:"))
        layout.addWidget(self.title_edit)
        layout.addWidget(QLabel("Isi Pesan:"))
        layout.addWidget(self.body_edit)
        layout.addWidget(self.important_check)
        layout.addLayout(actions)
        layout.addWidget(self.status_label)

    def _on_save(self) -> None:
        judul = self.title_edit.text().strip()
        isi = self.body_edit.toPlainText()
        if not judul or not isi:
            self.status_label.setText("Judul dan isi wajib diisi.")
            return
        try:
            self._store.add_message(
                owner_id=self._owner_id,
                judul=judul,
                isi=isi,
                is_penting=self.important_check.isChecked(),
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Gagal menyimpan", str(exc))
            return
        self.title_edit.clear()
        self.body_edit.clear()
        self.important_check.setChecked(False)
        self.status_label.setText("Pesan tersimpan.")
        self.saved.emit()


class ViewMessagesPanel(QWidget):
    """Sub-tab Lihat Pesan: tabel + lihat isi terpilih."""

    def __init__(self, store: MessageStore, owner_id: int, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = store
        self._owner_id = owner_id

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Judul", "Penting", "Tanggal"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Isi pesan yang dipilih akan tampil di sini…")

        self.refresh_btn = QPushButton("Muat Ulang")
        self.view_btn = QPushButton("Lihat Isi Terpilih")
        self.reveal_btn = QPushButton("Tampilkan Isi Asli")
        self.reveal_btn.setObjectName("secondaryBtn")
        self.reveal_btn.hide()
        self.status_label = QLabel("Siap.")

        self._current_id: Optional[int] = None
        self._is_penting = False
        self._showing_plain = False

        self.refresh_btn.clicked.connect(self.refresh)
        self.view_btn.clicked.connect(self._on_view)
        self.reveal_btn.clicked.connect(self._on_reveal)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.refresh_btn)
        actions.addWidget(self.view_btn)
        actions.addWidget(self.reveal_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(actions)
        layout.addWidget(QLabel("Isi Pesan:"))
        layout.addWidget(self.output_edit)
        layout.addWidget(self.status_label)

        self.refresh()

    def refresh(self) -> None:
        rows = self._store.list_messages(self._owner_id)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(row["judul"]))
            self.table.setItem(i, 2, QTableWidgetItem("Ya" if row["is_penting"] else "Tidak"))
            self.table.setItem(i, 3, QTableWidgetItem(row["dibuat_pada"]))
        self.status_label.setText(f"{len(rows)} pesan dimuat.")

    def _selected_id(self) -> Optional[int]:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _on_view(self) -> None:
        message_id = self._selected_id()
        if message_id is None:
            self.status_label.setText("Pilih satu baris pesan lebih dulu.")
            return
        try:
            payload, penting = self._store.get_payload(
                owner_id=self._owner_id, message_id=message_id
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Gagal membaca pesan", str(exc))
            return

        self._current_id = message_id
        self._is_penting = penting
        self._showing_plain = False

        if penting:
            self.output_edit.setPlainText(base64.b64encode(payload).decode("ascii"))
            self.reveal_btn.show()
            self.reveal_btn.setText("Tampilkan Isi Asli")
            self.status_label.setText("Menampilkan ciphertext — pesan tersimpan sebagai AES-GCM.")
        else:
            try:
                plain = self._store.get_plain(
                    owner_id=self._owner_id, message_id=message_id
                )
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(self, "Gagal membaca pesan", str(exc))
                return
            self.output_edit.setPlainText(plain)
            self.reveal_btn.hide()
            self.status_label.setText("Menampilkan isi — pesan tidak dienkripsi tambahan (hanya SQLCipher).")

    def _on_reveal(self) -> None:
        if self._current_id is None or not self._is_penting:
            return
        try:
            if self._showing_plain:
                payload, _ = self._store.get_payload(
                    owner_id=self._owner_id, message_id=self._current_id
                )
                self.output_edit.setPlainText(base64.b64encode(payload).decode("ascii"))
                self.reveal_btn.setText("Tampilkan Isi Asli")
                self._showing_plain = False
                self.status_label.setText("Menampilkan ciphertext — pesan tersimpan sebagai AES-GCM.")
            else:
                plain = self._store.get_plain(
                    owner_id=self._owner_id, message_id=self._current_id
                )
                self.output_edit.setPlainText(plain)
                self.reveal_btn.setText("Tampilkan Ciphertext")
                self._showing_plain = True
                self.status_label.setText("Menampilkan hasil dekripsi teks asli.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Gagal", str(exc))


class DbTab(QWidget):
    """Tab utama berisi sub-tab Tambah Pesan & Lihat Pesan."""

    def __init__(
        self,
        store: MessageStore,
        owner_id: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.add_panel = AddMessagePanel(store, owner_id)
        self.view_panel = ViewMessagesPanel(store, owner_id)
        self.add_panel.saved.connect(self.view_panel.refresh)

        tabs = QTabWidget()
        tabs.addTab(self.add_panel, "Tambah Pesan")
        tabs.addTab(self.view_panel, "Lihat Pesan")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tabs)
