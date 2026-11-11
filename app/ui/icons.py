"""Helper ikon SVG inline — dapat diwarnai ulang mengikuti tema.

Ikon disimpan sebagai SVG garis sederhana dengan placeholder `{stroke}`;
warna diganti saat render sehingga selaras dengan tema terang/gelap.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

_ICON_DIR = Path(__file__).resolve().parent / "assets" / "icons"


def load_pixmap(name: str, color: str = "#0F172A", size: int = 24) -> QPixmap:
    """Render ikon SVG ke QPixmap dengan warna stroke tertentu."""
    svg = (_ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
    data = svg.replace("{stroke}", color).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(data))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def load_icon(name: str, color: str = "#0F172A", size: int = 24) -> QIcon:
    return QIcon(load_pixmap(name, color, size))
