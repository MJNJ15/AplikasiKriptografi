"""Tab Basis Data: simpan/tampilkan pesan (penting vs biasa) — §4.6.

Menggunakan `MessageStore` (SQLCipher + AES-GCM per-rekor utk penting).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..db.database import MessageStore


class DbTab(QWidget):
    def __init__(
        self,
        store: MessageStore,
        owner_id: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._store = store
        self._owner_id = owner_id

        self.title_edit = self._make_line_edit("Judul pesan…")
        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText("Isi pesan…")
        self.important_check = QCheckBox("Pesan penting (enkripsi tambahan)")
        self.save_btn = QPushButton("Simpan Pesan")
        self.refresh_btn = QPushButton("Muat Ulang")
        self.view_btn = QPushButton("Lihat Isi Terpilih")
        self.status_label = QLabel("Siap.")

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Judul", "Penting", "Tanggal"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.save_btn.clicked.connect(self._on_save)
        self.refresh_btn.clicked.connect(self.refresh)
        self.view_btn.clicked.connect(self._on_view)

        actions = QHBoxLayout()
        actions.addWidget(self.save_btn)
        actions.addWidget(self.refresh_btn)
        actions.addWidget(self.view_btn)
        actions.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title_edit)
        layout.addWidget(self.body_edit)
        layout.addWidget(self.important_check)
        layout.addLayout(actions)
        layout.addWidget(self.table)
        layout.addWidget(self.status_label)

        self.refresh()

    @staticmethod
    def _make_line_edit(placeholder: str):
        from PySide6.QtWidgets import QLineEdit

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        return edit

    def refresh(self) -> None:
        rows = self._store.list_messages(self._owner_id)
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(row["judul"]))
            self.table.setItem(i, 2, QTableWidgetItem("Ya" if row["is_penting"] else "Tidak"))
            self.table.setItem(i, 3, QTableWidgetItem(row["dibuat_pada"]))
        self.status_label.setText(f"{len(rows)} pesan dimuat.")

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
        self.refresh()

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
            plain = self._store.get_plain(owner_id=self._owner_id, message_id=message_id)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Gagal membaca pesan", str(exc))
            return
        self.body_edit.setPlainText(plain)
        self.status_label.setText(f"Menampilkan isi pesan #{message_id}.")
