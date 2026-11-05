"""Biometrik wajah via webcam (LBPH + Haar cascade) — §4.2.

Pendaftaran: deteksi wajah (Haar) → normalisasi → latih LBPH (label 1).
Login: prediksi LBPH → jarak (confidence) vs ambang batas → cocok.
Liveness ringan: heuristik kedipan (mata terdeteksi lalu hilang).

Catatan: wheel opencv-contrib ≥ 5 tidak menyertakan berkas cascade; file XML
diunduh dari repo OpenCV ke `data/` (lihat README). OpenCV contrib diperlukan
untuk cv2.face.LBPHFaceRecognizer_create.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Sequence

import cv2
import numpy as np

FACE_SIZE = (100, 100)
# Hasil diagnostik webcam (lihat catatan): confidence self-match ~116–128,
# sehingga default 80 terlalu ketat. 150 memberi margin untuk cahaya/pose.
DEFAULT_MATCH_THRESHOLD = 150.0
EYE_MIN_SIZE = (20, 20)

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_FACE_CASCADE = _DEFAULT_DATA_DIR / "haarcascade_frontalface_default.xml"
DEFAULT_EYE_CASCADE = _DEFAULT_DATA_DIR / "haarcascade_eye.xml"


class FaceBiometrics:
    def __init__(
        self,
        threshold: float = DEFAULT_MATCH_THRESHOLD,
        face_cascade: str | Path | None = None,
        eye_cascade: str | Path | None = None,
    ) -> None:
        self._face_cascade = cv2.CascadeClassifier(
            str(face_cascade or DEFAULT_FACE_CASCADE)
        )
        self._eye_cascade = cv2.CascadeClassifier(
            str(eye_cascade or DEFAULT_EYE_CASCADE)
        )
        self._recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.threshold = threshold
        self._trained = False
        self._samples: list[np.ndarray] = []

    @staticmethod
    def to_gray(frame: np.ndarray) -> np.ndarray:
        if frame.ndim == 3:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame

    @staticmethod
    def normalize_face(gray: np.ndarray) -> np.ndarray:
        """Resize + equalize — dapat dipakai langsung tanpa deteksi Haar."""
        face = cv2.resize(gray, FACE_SIZE)
        return cv2.equalizeHist(face)

    def detect_faces(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        gray = self.to_gray(frame)
        rects = self._face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(64, 64)
        )
        return [(int(x), int(y), int(w), int(h)) for x, y, w, h in rects]

    def extract_face(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Deteksi wajah pertama → crop → normalize. None jika tidak ada wajah."""
        rects = self.detect_faces(frame)
        if not rects:
            return None
        x, y, w, h = rects[0]
        gray = self.to_gray(frame)
        return self.normalize_face(gray[y : y + h, x : x + w])

    def enroll(self, frames: Sequence[np.ndarray]) -> None:
        """Latih template dari beberapa frame. Semua diberi label 1."""
        grays = [
            self.normalize_face(self.to_gray(f))
            for f in frames
            if f is not None and f.size
        ]
        if not grays:
            raise ValueError("tidak ada wajah yang bisa didaftarkan")
        labels = np.zeros(len(grays), dtype=int)
        self._samples = grays
        self._recognizer.train(grays, labels)
        self._trained = True

    def save_template(self) -> bytes:
        """Serialisasi template (sampel wajah normalisasi) untuk disimpan
        (mis. dienkripsi lalu disimpan di DB)."""
        if not self._samples:
            raise RuntimeError("belum ada template wajah (enroll dulu)")
        buf = io.BytesIO()
        np.savez(buf, images=np.stack(self._samples))
        return buf.getvalue()

    def load_template(self, blob: bytes) -> None:
        """Muat template hasil save_template dan latih ulang recognizer."""
        data = np.load(io.BytesIO(blob))
        images = data["images"]
        if images.ndim != 3:
            raise ValueError("template wajah tidak valid")
        self._samples = [images[i] for i in range(images.shape[0])]
        labels = np.zeros(len(self._samples), dtype=int)
        self._recognizer.train(self._samples, labels)
        self._trained = True

    def predict(self, frame: np.ndarray) -> tuple[int, float]:
        """Kembalikan (label, confidence). Confidence kecil = lebih cocok."""
        if not self._trained:
            raise RuntimeError("belum ada template wajah (enroll dulu)")
        gray = self.normalize_face(self.to_gray(frame))
        label, conf = self._recognizer.predict(gray)
        return int(label), float(conf)

    def is_match(self, frame: np.ndarray) -> bool:
        _, conf = self.predict(frame)
        return conf <= self.threshold

    def blink_detected(self, frames: Sequence[np.ndarray]) -> bool:
        """Heuristik liveness ringan: setidaknya satu frame bermata, lalu
        satu frame tanpa mata (kedipan). Berguna untuk menolak foto diam.
        """
        seen_open = False
        for frame in frames:
            gray = self.to_gray(frame)
            eyes = self._eye_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=EYE_MIN_SIZE
            )
            if len(eyes) >= 2:
                seen_open = True
            elif seen_open:
                return True
        return False
