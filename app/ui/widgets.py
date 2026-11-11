"""Widget bersama UI: StatusLabel dengan state semantik (info/ok/error)."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QLabel, QWidget

_OK_WORDS = (
    "berhasil", "tersimpan", "valid", "dimuat", "dikenali",
    "siap", "ditampilkan", "tampil", "dicatat", "diperbarui",
)
_ERROR_WORDS = (
    "gagal", "wajib", "rusak", "salah", "tidak", "dibatalkan",
    "kosong", "invalid", "tidak valid", "tidak ditemukan",
)


class StatusLabel(QLabel):
    """Label status dengan state: info (default), ok (hijau), error (merah).

    `setText()` mengklasifikasikan pesan Indonesia secara otomatis; pemanggil
    juga dapat memakai `set_state()` untuk menetapkan state eksplisit.
    """

    def __init__(
        self,
        text: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self.setObjectName("statusLabel")
        self._state = "info"
        self._apply_state()

    def setText(self, text: str) -> None:
        super().setText(text)
        state = self._classify(text)
        if state != self._state:
            self._state = state
            self._apply_state()

    def set_state(self, state: str, text: Optional[str] = None) -> None:
        if text is not None:
            super().setText(text)
        self._state = state if state in ("ok", "error", "info") else "info"
        self._apply_state()

    def success(self, text: str) -> None:
        self.set_state("ok", text)

    def error(self, text: str) -> None:
        self.set_state("error", text)

    def info(self, text: str) -> None:
        self.set_state("info", text)

    def ready(self, text: str = "Siap.") -> None:
        self.info(text)

    def state(self) -> str:
        return self._state

    def _apply_state(self) -> None:
        self.setProperty("state", self._state)
        style = self.style()
        style.unpolish(self)
        style.polish(self)

    @classmethod
    def _classify(cls, text: str) -> str:
        low = text.lower().strip()
        if any(word in low for word in _ERROR_WORDS):
            return "error"
        if any(word in low for word in _OK_WORDS):
            return "ok"
        return "info"
