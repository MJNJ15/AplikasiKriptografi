"""Dialog webcam untuk menyimpan (enroll) & verifikasi wajah.

- EnrollFaceDialog: video live; pengguna menekan tombol "Simpan Wajah"
  untuk menyimpan template (beberapa frame diambil saat tombol ditekan).
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

        self._footer = QHBoxLayout()
        self._footer.addStretch(1)
        self._footer.addWidget(self.cancel_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self._camera)
        layout.addLayout(self._footer)

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
        self.template_bytes: Optional[bytes] = None

        self.simpan_btn = QPushButton("Simpan Wajah")
        self.simpan_btn.setObjectName("primaryBtn")
        self.simpan_btn.clicked.connect(self._on_save)
        idx = self._footer.indexOf(self.cancel_btn)
        self._footer.insertWidget(idx, self.simpan_btn)

        self._camera.status_label.setText(
            "Arahkan wajah ke kamera, lalu tekan 'Simpan Wajah'."
        )

    def _on_save(self) -> None:
        if self.template_bytes is not None:
            return
        frames = self._camera.grab_frames(NEEDED_FRAMES)
        faces = [
            f
            for f in (self._bio.extract_face(fr) for fr in frames)
            if f is not None
        ]
        if not faces:
            self._camera.status_label.setText("Wajah tidak terdeteksi — coba lagi.")
            return
        try:
            self._bio.enroll(faces)
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
