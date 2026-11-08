"""Dialog webcam untuk menyimpan (capture) & verifikasi wajah.

- CaptureFaceDialog: preview live untuk menyesuaikan posisi wajah; tombol
  "Simpan Foto" mengambil beberapa frame → enroll → template raw.
- VerifyFaceDialog: preview live; kotak deteksi hijau + persentase
  kemiripan terhadap template username; lulus bila ≥ threshold.

Keduanya memakai CameraWidget (kotak deteksi digambar oleh overlay).
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

CAPTURE_FRAMES = 10
VERIFY_TIMEOUT_SECONDS = 20.0
VERIFY_CONSECUTIVE = 3


class _FacePopupBase(QDialog):
    def __init__(
        self,
        title: str,
        camera_index: int,
        parent: Optional[QWidget],
        capture_factory,
        bio: FaceBiometrics,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(500, 460)

        self._bio = bio
        self._camera = CameraWidget(
            camera_index=camera_index,
            capture_factory=capture_factory,
            overlay_fn=bio.draw_detection_frame,
        )
        self._camera.frame_ready.connect(self._on_frame)

        self.cancel_btn = QPushButton("Batal")
        self.cancel_btn.clicked.connect(self.reject)

        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(self.cancel_btn)
        self._footer = footer

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


class CaptureFaceDialog(_FacePopupBase):
    """Kriteria #1: preview + tombol 'Simpan Foto'."""

    def __init__(
        self,
        camera_index: int = 0,
        parent: Optional[QWidget] = None,
        capture_factory=None,
    ) -> None:
        super().__init__("Simpan Wajah", camera_index, parent, capture_factory, FaceBiometrics())
        self.template_bytes: Optional[bytes] = None

        self.save_btn = QPushButton("Simpan Foto")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._on_save)
        self._footer.insertWidget(self._footer.indexOf(self.cancel_btn), self.save_btn)

        self._camera.status_label.setText("Arahkan wajah ke kamera, lalu tekan 'Simpan Foto'.")

    def _on_frame(self, frame) -> None:
        boxes = self._bio.detect_faces(frame)
        if boxes:
            self._camera.status_label.setText("✅ Wajah terdeteksi — tekan 'Simpan Foto'.")
        else:
            self._camera.status_label.setText("Tidak ada wajah terdeteksi — atur posisi.")

    def _on_save(self) -> None:
        if self.template_bytes is not None:
            return
        frames = self._camera.grab_frames(CAPTURE_FRAMES)
        try:
            self._bio.enroll(frames)
        except ValueError as exc:
            self._camera.status_label.setText(str(exc))
            return
        self.template_bytes = self._bio.save_template()
        self._camera.status_label.setText("Foto tersimpan — template dibuat.")
        self._camera.release_camera()
        self.accept()


class VerifyFaceDialog(_FacePopupBase):
    """Kriteria #2 & #3: preview + kotak + persentase kemiripan."""

    def __init__(
        self,
        template_raw: bytes,
        camera_index: int = 0,
        parent: Optional[QWidget] = None,
        capture_factory=None,
    ) -> None:
        bio = FaceBiometrics()
        bio.load_template(template_raw)
        super().__init__("Verifikasi Wajah", camera_index, parent, capture_factory, bio)

        self._deadline = time.monotonic() + VERIFY_TIMEOUT_SECONDS
        self._consecutive = 0
        self._camera.status_label.setText("Mencocokkan wajah…")

    def _on_frame(self, frame) -> None:
        if time.monotonic() > self._deadline:
            self._fail("Waktu habis — wajah tidak dikenali.")
            return

        passed, detected, percent, emb = self._bio.match(frame)
        if detected:
            color = (0, 255, 0) if passed else (0, 180, 255)
            self._camera.set_overlay(
                lambda f: self._bio.draw_detection(
                    f, self._bio.detect_faces(f), f"Kemiripan: {percent:.0f}%", color
                )
            )
            if passed:
                self._consecutive += 1
                self._camera.status_label.setText(
                    f"Kemiripan {percent:.0f}% — wajah dikenali ({self._consecutive}/{VERIFY_CONSECUTIVE})."
                )
                if self._consecutive >= VERIFY_CONSECUTIVE:
                    self._camera.status_label.setText("✅ Wajah cocok!")
                    self._camera.release_camera()
                    self.accept()
            else:
                self._consecutive = 0
                self._camera.status_label.setText(
                    f"Kemiripan {percent:.0f}% (di bawah ambang)."
                )
        else:
            self._consecutive = 0
            self._camera.status_label.setText("Tidak ada wajah — arahkan ke kamera.")
