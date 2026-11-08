"""Biometrik wajah — OpenCV DNN (YUNet + SFace) + CLAHE.

Deteksi wajah: YUNet (ONNX) — kotak pembatas + skor keypoint.
Ciri wajah: SFace (ONNX) — embedding 128-d.
Kemiripan: cosine similarity → persentase (0–100%).

Tahan perubahan kecerahan (kriteria #4): setiap crop wajah dinormalisasi
dengan CLAHE (Contrast Limited Adaptive Histogram Equalization) pada
saluran Value HSV sebelum masuk SFace, ditambah sifat DNN yang robust.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Sequence

import cv2
import numpy as np

DETECT_INPUT = (320, 320)
DETECT_SCORE_THRESHOLD = 0.8
EMBED_SIZE = (112, 112)
DEFAULT_MATCH_THRESHOLD = 0.45  # cosine similarity (0–1); >0.45 = cocok
CLAHE_CLIP = 3.0
CLAHE_GRID = (8, 8)

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_DETECTOR_MODEL = _DEFAULT_DATA_DIR / "face_detection_yunet_2023mar.onnx"
DEFAULT_RECOGNIZER_MODEL = _DEFAULT_DATA_DIR / "face_recognition_sface_2021dec.onnx"


class FaceBiometrics:
    def __init__(
        self,
        threshold: float = DEFAULT_MATCH_THRESHOLD,
        detector_model: str | Path | None = None,
        recognizer_model: str | Path | None = None,
    ) -> None:
        detector_path = str(detector_model or DEFAULT_DETECTOR_MODEL)
        recognizer_path = str(recognizer_model or DEFAULT_RECOGNIZER_MODEL)
        for p in (detector_path, recognizer_path):
            if not Path(p).exists():
                raise FileNotFoundError(f"model tidak ditemukan: {p}")

        self._detector = cv2.FaceDetectorYN.create(
            detector_path,
            "",
            DETECT_INPUT,
            score_threshold=DETECT_SCORE_THRESHOLD,
        )
        self._recognizer = cv2.FaceRecognizerSF.create(recognizer_path, "")
        self.threshold = threshold
        self._clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=CLAHE_GRID)
        self._template_emb: Optional[np.ndarray] = None
        self._template_count = 0

    # ---------------------------------------------------------------- deteksi
    def detect_faces(self, frame: np.ndarray) -> list[tuple[int, int, int, int]]:
        """Kembalikan daftar (x, y, w, h) wajah yang terdeteksi."""
        if frame.ndim == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        # YUNet membutuhkan size input sesuai frame aktual.
        h, w = frame.shape[:2]
        self._detector.setInputSize((w, h))
        result = self._detector.detect(frame)
        # OpenCV 5: hasil tuple (jumlah, faces); versi lain: faces langsung.
        if isinstance(result, tuple) and len(result) >= 2:
            faces = result[1]
        else:
            faces = result
        if faces is None:
            return []
        try:
            count = len(faces)
        except TypeError:
            return []
        if count == 0:
            return []
        boxes = []
        for face in faces:
            x, y, w, h = (int(v) for v in face[:4])
            boxes.append((x, y, w, h))
        return boxes

    # ------------------------------------------------------------ preprocessing
    def normalize_lighting(self, bgr_crop: np.ndarray) -> np.ndarray:
        """CLAHE pada saluran Value HSV — perata pencahayaan."""
        hsv = cv2.cvtColor(bgr_crop, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = self._clahe.apply(hsv[:, :, 2])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # ------------------------------------------------------------ ekstraksi
    def extract_face_rgb(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Crop wajah pertama → normalisasi cahaya → 112×112 RGB."""
        boxes = self.detect_faces(frame)
        if not boxes:
            return None
        x, y, w, h = boxes[0]
        crop = frame[y : y + h, x : x + w]
        if crop.size == 0:
            return None
        crop = self.normalize_lighting(crop)
        crop = cv2.resize(crop, EMBED_SIZE, interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

    def embedding(self, rgb: np.ndarray) -> np.ndarray:
        """Embedding 128-d (dinormalisasi L2)."""
        feat = self._recognizer.feature(rgb)
        emb = np.array(feat, dtype=np.float32).reshape(-1)
        norm = np.linalg.norm(emb)
        return emb / norm if norm > 0 else emb

    def extract_embedding(self, frame: np.ndarray) -> Optional[np.ndarray]:
        rgb = self.extract_face_rgb(frame)
        if rgb is None:
            return None
        return self.embedding(rgb)

    # ------------------------------------------------------------ kemiripan
    @staticmethod
    def cosine(a: np.ndarray, b: np.ndarray) -> float:
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def similarity_percent(self, emb_live: np.ndarray) -> float:
        if self._template_emb is None:
            return 0.0
        sim = self.cosine(emb_live, self._template_emb)
        return max(0.0, sim) * 100.0

    def match(self, frame: np.ndarray) -> tuple[bool, bool, float, Optional[np.ndarray]]:
        """(lulus, wajah_terdeteksi, persen, embedding_live).

        `lulus=True` bila persentase ≥ threshold (0–100 → threshold*100).
        """
        emb = self.extract_embedding(frame)
        if emb is None:
            return False, False, 0.0, None
        percent = self.similarity_percent(emb)
        return percent >= self.threshold * 100.0, True, percent, emb

    # ------------------------------------------------------------ template
    def enroll(self, frames: Sequence[np.ndarray]) -> None:
        """Rata-ratakan embedding dari frame yang berisi wajah → template."""
        embs = [
            e
            for f in frames
            if f is not None and f.size
            for e in [self.extract_embedding(f)]
            if e is not None
        ]
        if not embs:
            raise ValueError("tidak ada wajah yang terdeteksi")
        mean = np.mean(np.stack(embs), axis=0)
        norm = np.linalg.norm(mean)
        self._template_emb = mean / norm if norm > 0 else mean
        self._template_count = len(embs)

    def save_template(self) -> bytes:
        if self._template_emb is None:
            raise RuntimeError("belum ada template (enroll dulu)")
        buf = io.BytesIO()
        np.savez(buf, emb=self._template_emb, count=self._template_count)
        return buf.getvalue()

    def load_template(self, blob: bytes) -> None:
        data = np.load(io.BytesIO(blob))
        self._template_emb = data["emb"].astype(np.float32).reshape(-1)
        self._template_count = int(data["count"])
        if self._template_emb.size == 0:
            raise ValueError("template tidak valid")

    def has_template(self) -> bool:
        return self._template_emb is not None

    # ------------------------------------------------------------ gambar overlay
    def draw_detection_frame(
        self,
        frame_bgr: np.ndarray,
        label: str = "",
        color: tuple[int, int, int] = (0, 255, 0),
    ) -> np.ndarray:
        """Deteksi wajah di frame lalu gambar kotak + label (BGR)."""
        boxes = self.detect_faces(frame_bgr)
        return self.draw_detection(frame_bgr, boxes, label, color)

    @staticmethod
    def draw_detection(
        frame_bgr: np.ndarray,
        boxes: Sequence[tuple[int, int, int, int]],
        label: str = "",
        color: tuple[int, int, int] = (0, 255, 0),
    ) -> np.ndarray:
        """Salin frame + gambar kotak deteksi & label (BGR)."""
        out = frame_bgr.copy()
        for x, y, w, h in boxes:
            cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
        if label:
            cv2.putText(
                out,
                label,
                (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2,
                cv2.LINE_AA,
            )
        return out
