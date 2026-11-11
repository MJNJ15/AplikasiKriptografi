"""Helper animasi UI (PySide6): fade-in, cross-fade, dan pulse.

Qt Style Sheets tidak mendukung transisi CSS, jadi semua animasi memakai
QPropertyAnimation + QGraphicsOpacityEffect. Efek dibuang setelah selesai
agar tidak ada overhead komposisi permanen.
"""

from __future__ import annotations

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

FADE_MS = 300
REVEAL_MS = 240
PULSE_MS = 520
PULSE_LOW = 0.35


def _opacity_effect(widget: QWidget) -> QGraphicsOpacityEffect:
    effect = widget.graphicsEffect()
    if isinstance(effect, QGraphicsOpacityEffect):
        return effect
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    return effect


def _release_when_done(widget: QWidget, effect: QGraphicsOpacityEffect, anim: QPropertyAnimation) -> None:
    """Lepas efek sesudah animasi selesai (hindari biaya komposisi).

    QWidget.setGraphicsEffect(None) sudah menghapus efek lama, jadi tidak
    perlu deleteLater lagi.
    """

    def cleanup() -> None:
        try:
            if widget.graphicsEffect() is effect:
                widget.setGraphicsEffect(None)
        except RuntimeError:
            pass

    anim.finished.connect(cleanup)


def _stop_previous(widget: QWidget) -> None:
    prev = getattr(widget, "_anim_ref", None)
    if prev is not None and prev.state() == QAbstractAnimation.State.Running:
        prev.stop()


def _start(widget: QWidget, anim: QPropertyAnimation) -> QPropertyAnimation:
    _stop_previous(widget)
    widget._anim_ref = anim  # type: ignore[attr-defined]
    anim.start()
    return anim


def fade_in(widget: QWidget, ms: int = FADE_MS) -> QPropertyAnimation:
    """Fade lembut dari transparan ke penuh saat widget pertama tampil."""
    effect = _opacity_effect(widget)
    effect.setOpacity(0.0)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    _release_when_done(widget, effect, anim)
    return _start(widget, anim)


def fade_reveal(widget: QWidget, ms: int = REVEAL_MS) -> QPropertyAnimation:
    """Cross-fade halus untuk isi halaman (mis. ganti tab)."""
    effect = _opacity_effect(widget)
    effect.setOpacity(0.0)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(ms)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutQuad)
    _release_when_done(widget, effect, anim)
    return _start(widget, anim)


def pulse(widget: QWidget, ms: int = PULSE_MS, low: float = PULSE_LOW) -> QPropertyAnimation:
    """Kedip singkat 1 → low → 1 untuk menarik perhatian (mis. status)."""
    effect = _opacity_effect(widget)
    effect.setOpacity(1.0)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(ms)
    anim.setKeyValueAt(0.0, 1.0)
    anim.setKeyValueAt(0.5, low)
    anim.setKeyValueAt(1.0, 1.0)
    _release_when_done(widget, effect, anim)
    return _start(widget, anim)
