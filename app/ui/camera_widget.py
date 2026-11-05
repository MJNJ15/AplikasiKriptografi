"""Widget webcam live (floating/pop-up) untuk biometrik wajah.

Menampilkan video real-time, overlay kotak deteksi (opsional), dan label
indikator status. Frame BGR dipancarkan via `frame_ready` ke konsumen
(pop enroll/verifikasi).
"""

from __future__ import annotations

from typing import Callable, Optional

import cv2
import numpy as np

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

VIDEO_WIDTH = 420
VIDEO_HEIGHT = 300


def default_capture_factory(index: int):
    return cv2.VideoCapture(index)


class CameraWidget(QWidget):
    """Video preview + frame_ready. `detector` opsional: frame → list rects."""

    frame_ready = Signal(object)  # np.ndarray BGR

    def __init__(
        self,
        camera_index: int = 0,
        parent: Optional[QWidget] = None,
        capture_factory: Optional[Callable[[int], object]] = None,
        detector: Optional[Callable[[np.ndarray], list]] = None,
        status_text: str = "Webcam menyala…",
    ) -> None:
        super().__init__(parent)
        self._camera_index = camera_index
        self._capture_factory = capture_factory or default_capture_factory
        self._detector = detector
        self._cap = None
        self._latest_frame: Optional[np.ndarray] = None

        self.video_label = QLabel("Menyiapkan webcam…")
        self.video_label.setFixedSize(VIDEO_WIDTH, VIDEO_HEIGHT)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background:#000; color:#fff; border-radius:8px;")

        self.status_label = QLabel(status_text)
        self.status_label.setObjectName("fieldLabel")

        layout = QVBoxLayout(self)
        layout.addWidget(self.video_label)
        layout.addWidget(self.status_label)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self.step)

    def start(self) -> None:
        if self._cap is None:
            self._cap = self._capture_factory(self._camera_index)
        if self._cap is not None and self._cap.isOpened():
            self._timer.start()
            self.status_label.setText("Webcam menyala…")
        else:
            self.status_label.setText("Webcam tidak tersedia.")

    def stop(self) -> None:
        self._timer.stop()

    def release_camera(self) -> None:
        self.stop()
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def latest_frame(self) -> Optional[np.ndarray]:
        return self._latest_frame

    def step(self) -> None:
        if self._cap is None or not self._cap.isOpened():
            return
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return
        self._latest_frame = frame

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if self._detector is not None:
            try:
                for x, y, w, h in self._detector(frame):
                    cv2.rectangle(rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)
            except Exception:
                pass

        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        )
        self.frame_ready.emit(frame)

    def closeEvent(self, event) -> None:
        self.release_camera()
        super().closeEvent(event)
