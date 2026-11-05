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
QPushButton#themeToggle {{
    background: #eceef5;
    color: #344054;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#themeToggle:hover {{
    background: #dfe4f2;
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


def apply_theme(app: QApplication, dark: bool = False) -> None:
    """Terapkan tema global: Fusion + palet + QSS (terang/gelap)."""
    global _dark_mode
    _dark_mode = dark
    app.setStyle("Fusion")

    if dark:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1e222b"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#e6e9f0"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#262b36"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#e6e9f0"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#353c4a"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e6e9f0"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#6c8bff"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8a94a8"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2b313d"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e6e9f0"))
        app.setPalette(palette)
        app.setStyleSheet(_QSS_DARK)
    else:
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


_dark_mode = False


def is_dark() -> bool:
    return _dark_mode


def toggle_theme(app: QApplication) -> bool:
    """Balik mode gelap/terang; kembalikan state baru."""
    apply_theme(app, dark=not is_dark())
    return is_dark()


def make_theme_toggle_button():
    """Tombol toggle kecil (dipakai di pojok kanan bawah tiap window)."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton

    btn = QPushButton("Mode Gelap" if not is_dark() else "Mode Terang")
    btn.setObjectName("themeToggle")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_click() -> None:
        toggle_theme(QApplication.instance())
        btn.setText("Mode Gelap" if not is_dark() else "Mode Terang")

    btn.clicked.connect(_on_click)
    return btn


_QSS_DARK = f"""
QWidget {{
    font-family: "Segoe UI";
    font-size: 13px;
    color: #e6e9f0;
}}
QMainWindow, QDialog {{
    background: #1e222b;
}}
QLabel {{
    background: transparent;
    color: #e6e9f0;
}}

QTabWidget::pane {{
    border: none;
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: #9aa4b8;
    padding: 10px 18px;
    margin-right: 2px;
    border-radius: 8px 8px 0 0;
    font-weight: 500;
}}
QTabBar::tab:hover {{
    background: #2a303c;
}}
QTabBar::tab:selected {{
    background: {ACCENT};
    color: #ffffff;
}}

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
    background: #3a4150;
    color: #6a7285;
}}

QLineEdit, QPlainTextEdit, QComboBox {{
    background: #262b36;
    border: 1px solid #3a4150;
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: #6c8bff;
    selection-color: #ffffff;
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid #6c8bff;
}}
QPlainTextEdit {{
    padding: 8px;
}}

QCheckBox {{
    spacing: 8px;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #4a5265;
    background: #262b36;
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

QTableWidget {{
    background: #262b36;
    border: 1px solid #3a4150;
    border-radius: 8px;
    gridline-color: #313846;
    selection-background-color: #39415a;
    selection-color: #ffffff;
}}
QHeaderView::section {{
    background: #2f3542;
    border: none;
    border-bottom: 1px solid #3a4150;
    padding: 6px 10px;
    font-weight: 600;
    color: #b8c0d4;
}}

QGroupBox {{
    border: 1px solid #3a4150;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 6px;
}}
QMessageBox {{
    background: #1e222b;
}}
QStatusBar {{
    background: #20252f;
    color: #9aa4b8;
}}

#loginCard {{
    background: #262b36;
    border: 1px solid #3a4150;
    border-radius: 16px;
}}
#titleLabel {{
    font-size: 24px;
    font-weight: 700;
    color: #f2f4f9;
}}
#subtitleLabel {{
    color: #9aa4b8;
    font-size: 13px;
}}
#fieldLabel {{
    font-weight: 600;
    color: #c8d0e2;
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
    background: #353c4a;
    color: #cdd4e3;
    min-height: 42px;
    font-size: 14px;
}}
QPushButton#secondaryBtn:hover {{
    background: #404859;
}}
#statusLabel {{
    color: #8a94a8;
    font-size: 12px;
}}
QPushButton#themeToggle {{
    background: #353c4a;
    color: #cdd4e3;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#themeToggle:hover {{
    background: #404859;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #4a5265;
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #5a637a;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""
