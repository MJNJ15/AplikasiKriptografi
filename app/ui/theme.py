"""Tema modern terang untuk aplikasi (Fusion + palet + QSS global).

Dipanggil sekali setelah QApplication dibuat (lihat main.py). Aksen biru
#4f6ef7, latar abu lembut, karton putih, tombol membulat.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#4f6ef7"
ACCENT_DARK = "#3b5bde"
ACCENT_PRESSED = "#3451c4"

_QSS = f"""
QWidget {{
    font-family: "Segoe UI";
    font-size: 13px;
    color: #212b36;
}}
QMainWindow, QDialog {{
    background: #f5f6fa;
}}
QLabel {{
    background: transparent;
    color: #212b36;
}}

/* ---------- Tab ---------- */
QTabWidget::pane {{
    border: none;
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: #475467;
    padding: 10px 18px;
    margin-right: 2px;
    border-radius: 8px 8px 0 0;
    font-weight: 500;
}}
QTabBar::tab:hover {{
    background: #e9ecf8;
}}
QTabBar::tab:selected {{
    background: {ACCENT};
    color: #ffffff;
}}

/* ---------- Tombol ---------- */
QPushButton {{
    background: {ACCENT};
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {ACCENT_DARK};
}}
QPushButton:pressed {{
    background: {ACCENT_PRESSED};
}}
QPushButton:disabled {{
    background: #c2cad9;
    color: #f0f2f7;
}}

/* ---------- Input ---------- */
QLineEdit, QPlainTextEdit, QComboBox {{
    background: #ffffff;
    border: 1px solid #dfe3ec;
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: #dbe2ff;
    selection-color: #1c2540;
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {ACCENT};
}}
QPlainTextEdit {{
    padding: 8px;
}}

/* ---------- CheckBox ---------- */
QCheckBox {{
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #ccd3e3;
    background: #ffffff;
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

/* ---------- Tabel ---------- */
QTableWidget {{
    background: #ffffff;
    border: 1px solid #dfe3ec;
    border-radius: 8px;
    gridline-color: #eef0f6;
    selection-background-color: #dbe2ff;
    selection-color: #1c2540;
}}
QHeaderView::section {{
    background: #f0f2f8;
    border: none;
    border-bottom: 1px solid #dfe3ec;
    padding: 6px 10px;
    font-weight: 600;
    color: #344054;
}}

/* ---------- Group / Message / Status ---------- */
QGroupBox {{
    border: 1px solid #dfe3ec;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 6px;
}}
QMessageBox {{
    background: #f5f6fa;
}}
QStatusBar {{
    background: #eceef5;
    color: #475467;
}}

/* ---------- Login (card) ---------- */
#loginCard {{
    background: #ffffff;
    border: 1px solid #dfe3ec;
    border-radius: 16px;
}}
#titleLabel {{
    font-size: 24px;
    font-weight: 700;
    color: #212b36;
}}
#subtitleLabel {{
    color: #667085;
    font-size: 13px;
}}
#fieldLabel {{
    font-weight: 600;
    color: #344054;
}}
QLineEdit#inputField {{
    padding: 10px 12px;
    font-size: 14px;
    min-height: 22px;
}}
QPushButton#primaryBtn {{
    min-height: 42px;
    font-size: 14px;
}}
QPushButton#secondaryBtn {{
    background: #eef1f8;
    color: #344054;
    min-height: 42px;
    font-size: 14px;
}}
QPushButton#secondaryBtn:hover {{
    background: #dfe4f2;
}}
#statusLabel {{
    color: #98a2b3;
    font-size: 12px;
}}

/* ---------- Scrollbar ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #c7cede;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #aab3c9;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Terapkan tema global: Fusion + palet terang + QSS."""
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f5f6fa"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#212b36"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#212b36"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#eef0f6"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#212b36"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#98a2b3"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#212b36"))
    app.setPalette(palette)

    app.setStyleSheet(_QSS)
