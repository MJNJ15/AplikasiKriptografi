"""Dialog webcam untuk menyimpan (enroll) & verifikasi wajah.

- EnrollFaceDialog: otomatis menangkap beberapa frame saat wajah terdeteksi
  (video live), lalu menyimpan template raw ke `template_bytes`.
- VerifyFaceDialog: mencocokkan frame live terhadap template; cocok → accept.

Keduanya memakai CameraWidget (webcam menyala + indikator status).
"""

from __future__ import annotations

import time
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..security.biometric import FaceBiometrics
from .camera_widget import CameraWidget

NEEDED_FRAMES = 8
ENROLL_TIMEOUT_SECONDS = 25.0
VERIFY_TIMEOUT_SECONDS = 15.0


class _FacePopupBase(QDialog):
    def __init__(
        self,
        title: str,
        camera_index: int,
        parent: Optional[QWidget],
        capture_factory,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(480, 420)

        self._camera = CameraWidget(
            camera_index=camera_index,
            capture_factory=capture_factory,
            detector=FaceBiometrics().detect_faces,
        )
        self._camera.frame_ready.connect(self._on_frame)

        self.cancel_btn = QPushButton("Batal")
        self.cancel_btn.clicked.connect(self.reject)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(self.cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self._camera)
        layout.addLayout(footer)

        self._camera.start()

    def _on_frame(self, frame) -> None:
        raise NotImplementedError

    def _fail(self, msg: str) -> None:
        self._camera.status_label.setText(msg)
        self._camera.release_camera()
        self.reject()


class EnrollFaceDialog(_FacePopupBase):
    def __init__(
        self,
        camera_index: int = 0,
        parent: Optional[QWidget] = None,
        capture_factory=None,
    ) -> None:
        super().__init__("Simpan Wajah", camera_index, parent, capture_factory)
        self._bio = FaceBiometrics()
        self._collected: list = []
        self._deadline = time.monotonic() + ENROLL_TIMEOUT_SECONDS
        self.template_bytes: Optional[bytes] = None
        self._camera.status_label.setText("Mendeteksi wajah… arahkan wajah ke kamera")

    def _on_frame(self, frame) -> None:
        if self.template_bytes is not None:
            return
        if time.monotonic() > self._deadline:
            self._fail("Waktu habis — wajah tidak cukup terdeteksi.")
            return
        face = self._bio.extract_face(frame)
        if face is None:
            return
        self._collected.append(face)
        self._camera.status_label.setText(
            f"Merekam wajah… {len(self._collected)}/{NEEDED_FRAMES}"
        )
        if len(self._collected) >= NEEDED_FRAMES:
            self._finish_enroll()

    def _finish_enroll(self) -> None:
        try:
            self._bio.enroll(self._collected)
        except ValueError as exc:
            self._fail(str(exc))
            return
        self.template_bytes = self._bio.save_template()
        self._camera.status_label.setText("Template wajah tersimpan.")
        self._camera.release_camera()
        self.accept()


class VerifyFaceDialog(_FacePopupBase):
    def __init__(
        self,
        template_raw: bytes,
        camera_index: int = 0,
        parent: Optional[QWidget] = None,
        capture_factory=None,
    ) -> None:
        super().__init__("Verifikasi Wajah", camera_index, parent, capture_factory)
        self._bio = FaceBiometrics()
        self._bio.load_template(template_raw)
        self._deadline = time.monotonic() + VERIFY_TIMEOUT_SECONDS
        self._camera.status_label.setText("Mencocokkan wajah…")

    def _on_frame(self, frame) -> None:
        if time.monotonic() > self._deadline:
            self._fail("Waktu habis — wajah tidak dikenali.")
            return
        try:
            if self._bio.is_match(frame):
                self._camera.status_label.setText("Cocok! Wajah dikenali.")
                self._camera.release_camera()
                self.accept()
        except RuntimeError:
            pass
