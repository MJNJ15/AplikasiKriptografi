"""Tema Flat + Swiss untuk aplikasi (Fusion + palet + QSS global).

Palet mengikuti rasio 60/30/10 (direferensikan dari skill ui-ux-pro-max):
  60% main    — teal keamanan (#0D9488 family): tombol utama, tab aktif,
                 header bar, fokus input, status aktif.
  30% secondary — slate/netral: latar, kartu, tabel, tombol sekunder,
                 border, teks.
  10% accent  — oranye CTA (#EA580C family): aksi utama & penekanan.
Warna semantik (sukses/warning/error) berada di luar rasio dekoratif.

API publik: apply_theme(app, dark), is_dark(), toggle_theme(app),
make_theme_toggle_button(on_toggled), current_colors().
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QFontDatabase, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
)

# ---------------------------------------------------------------------------
# Token palet — 60/30/10 + semantik
# ---------------------------------------------------------------------------

_LIGHT = {
    # 30% secondary — surfaces & teks
    "bg": "#F4F7F9",
    "card": "#FFFFFF",
    "border": "#DCE5E8",
    "border_strong": "#C9D6DA",
    "text": "#0F172A",
    "text_muted": "#5B6B7A",
    "muted_bg": "#EAF1F3",
    "placeholder": "#8AA0AD",
    "alternate": "#F1F6F8",
    "disabled_bg": "#CBD5DB",
    "disabled_text": "#F2F6F8",
    # 60% main — teal keamanan
    "primary": "#0F766E",
    "primary_hover": "#0D9488",
    "primary_pressed": "#115E59",
    "primary_soft": "#CCFBF1",
    "on_primary": "#FFFFFF",
    "tab_selected_bg": "#0F766E",
    "tab_selected_fg": "#FFFFFF",
    # 10% accent — oranye CTA
    "accent": "#EA580C",
    "accent_hover": "#F97316",
    "accent_pressed": "#C2410C",
    "on_accent": "#FFFFFF",
    # Semantik
    "ok": "#16A34A",
    "warn": "#B45309",
    "err": "#DC2626",
    # Header
    "header_bg": "#0F766E",
    "header_text": "#FFFFFF",
    "header_muted": "rgba(255, 255, 255, 0.72)",
    "header_chip": "rgba(255, 255, 255, 0.14)",
    "header_chip_hover": "rgba(255, 255, 255, 0.28)",
    # Scrollbar
    "handle": "#B9C7CC",
    "handle_hover": "#9FB3BA",
    "scroll_track": "#E5EDF0",
}

_DARK = {
    # 30% secondary
    "bg": "#0E141A",
    "card": "#1B2330",
    "border": "#2C3744",
    "border_strong": "#3A495A",
    "text": "#E7EDF3",
    "text_muted": "#93A1B2",
    "muted_bg": "#222C39",
    "placeholder": "#6A7889",
    "alternate": "#1F2A38",
    "disabled_bg": "#33404F",
    "disabled_text": "#66758A",
    # 60% main
    "primary": "#14B8A6",
    "primary_hover": "#2DD4BF",
    "primary_pressed": "#0D9488",
    "primary_soft": "#17433D",
    "on_primary": "#05312C",
    "tab_selected_bg": "#14B8A6",
    "tab_selected_fg": "#05312C",
    # 10% accent
    "accent": "#F97316",
    "accent_hover": "#FB923C",
    "accent_pressed": "#EA580C",
    "on_accent": "#1A0E00",
    # Semantik
    "ok": "#4ADE80",
    "warn": "#FBBF24",
    "err": "#F87171",
    # Header
    "header_bg": "#0B3B36",
    "header_text": "#FFFFFF",
    "header_muted": "rgba(255, 255, 255, 0.68)",
    "header_chip": "rgba(255, 255, 255, 0.14)",
    "header_chip_hover": "rgba(255, 255, 255, 0.28)",
    # Scrollbar
    "handle": "#425163",
    "handle_hover": "#54677E",
    "scroll_track": "#1B2330",
}

# Akses cepat (kompatibilitas nama lama)
ACCENT = _LIGHT["primary"]
ACCENT_DARK = _LIGHT["primary_hover"]
ACCENT_PRESSED = _LIGHT["primary_pressed"]

_dark_mode = False
_FONT_FAMILY: Optional[str] = None
_cursor_filter: Optional[QObject] = None


class _CursorPolishFilter(QObject):
    """Tetapkan kursor via kode (QSS tidak mendukung properti `cursor`).

    Event `Polish` mengalir untuk semua widget, termasuk yang dibuat
    belakangan, sehingga satu filter ini menangani seluruh aplikasi.
    """

    def eventFilter(self, obj, event) -> bool:
        if event.type() == QEvent.Type.Polish:
            try:
                if isinstance(obj, (QPushButton, QCheckBox, QComboBox)):
                    obj.setCursor(Qt.CursorShape.PointingHandCursor)
                elif isinstance(obj, (QLineEdit, QPlainTextEdit)):
                    obj.setCursor(Qt.CursorShape.IBeamCursor)
            except RuntimeError:
                pass
        return False


def current_colors() -> dict:
    """Token palet aktif — dipakai untuk mewarnai ulang ikon saat ganti tema."""
    return _DARK if _dark_mode else _LIGHT


def primary_color() -> str:
    return current_colors()["primary"]


def accent_color() -> str:
    return current_colors()["accent"]


def text_color() -> str:
    return current_colors()["text"]


# ---------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------

def _register_font() -> None:
    global _FONT_FAMILY
    if _FONT_FAMILY is not None:
        return
    path = Path(__file__).resolve().parent / "assets" / "fonts" / "PlusJakartaSans.ttf"
    if not path.exists():
        _FONT_FAMILY = "Segoe UI"
        return
    try:
        index = QFontDatabase.addApplicationFont(str(path))
        families = QFontDatabase.applicationFontFamilies(index) if index >= 0 else []
        _FONT_FAMILY = families[0] if families else "Segoe UI"
    except Exception:  # noqa: BLE001
        _FONT_FAMILY = "Segoe UI"


# ---------------------------------------------------------------------------
# Generator QSS
# ---------------------------------------------------------------------------

def _build_qss(t: dict) -> str:
    font = _FONT_FAMILY or "Segoe UI"
    return f"""
QWidget {{
    font-family: "{font}";
    font-size: 13px;
    color: {t["text"]};
}}
QMainWindow, QDialog {{
    background: {t["bg"]};
}}
QLabel {{
    background: transparent;
    color: {t["text"]};
}}

/* ---------- Tab ---------- */
QTabWidget::pane {{
    border: 1px solid {t["border"]};
    border-radius: 10px;
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: {t["text_muted"]};
    padding: 10px 20px;
    margin-right: 2px;
    border-radius: 10px 10px 0 0;
    font-weight: 500;
}}
QTabBar::tab:hover {{
    background: {t["muted_bg"]};
}}
QTabBar::tab:selected {{
    background: {t["tab_selected_bg"]};
    color: {t["tab_selected_fg"]};
    font-weight: 700;
}}

/* ---------- Tombol ---------- */
QPushButton {{
    background: {t["primary"]};
    color: {t["on_primary"]};
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {t["primary_hover"]};
}}
QPushButton:pressed {{
    background: {t["primary_pressed"]};
    padding-top: 10px;
    padding-bottom: 6px;
}}
QPushButton:focus {{
    border: 2px solid {t["accent"]};
}}
QPushButton:disabled {{
    background: {t["disabled_bg"]};
    color: {t["disabled_text"]};
}}
QPushButton#accentBtn {{
    background: {t["accent"]};
    color: {t["on_accent"]};
}}
QPushButton#accentBtn:hover {{
    background: {t["accent_hover"]};
}}
QPushButton#accentBtn:pressed {{
    background: {t["accent_pressed"]};
}}

/* ---------- Input ---------- */
QLineEdit, QPlainTextEdit, QComboBox {{
    background: {t["card"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: {t["primary_soft"]};
    selection-color: {t["text"]};
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 1px solid {t["primary"]};
}}
QLineEdit[error="true"], QPlainTextEdit[error="true"], QComboBox[error="true"] {{
    border: 1px solid {t["err"]};
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
    border: 1px solid {t["border_strong"]};
    background: {t["card"]};
}}
QCheckBox::indicator:checked {{
    background: {t["primary"]};
    border-color: {t["primary"]};
}}

/* ---------- Tabel ---------- */
QTableWidget {{
    background: {t["card"]};
    alternate-background-color: {t["alternate"]};
    border: 1px solid {t["border"]};
    border-radius: 8px;
    gridline-color: {t["border"]};
    selection-background-color: {t["primary_soft"]};
    selection-color: {t["text"]};
}}
QHeaderView::section {{
    background: {t["muted_bg"]};
    border: none;
    border-bottom: 1px solid {t["border"]};
    padding: 6px 10px;
    font-weight: 600;
    color: {t["text_muted"]};
}}

/* ---------- Group / Frame / Status ---------- */
QGroupBox {{
    border: 1px solid {t["border"]};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 6px;
}}
QFrame#panelCard {{
    background: {t["card"]};
    border: 1px solid {t["border"]};
    border-radius: 12px;
}}
QMessageBox {{
    background: {t["bg"]};
}}
QStatusBar {{
    background: {t["muted_bg"]};
    color: {t["text_muted"]};
}}

QLabel#statusLabel {{
    color: {t["text_muted"]};
    font-size: 12px;
}}
QLabel#statusLabel[state="ok"] {{
    color: {t["ok"]};
    font-weight: 600;
}}
QLabel#statusLabel[state="error"] {{
    color: {t["err"]};
    font-weight: 600;
}}
QLabel#statusLabel[state="info"] {{
    color: {t["text_muted"]};
}}
QLabel#emptyHint {{
    color: {t["text_muted"]};
    font-size: 13px;
}}

/* ---------- Header aplikasi ---------- */
QFrame#appHeader {{
    background: {t["header_bg"]};
    border: none;
    border-radius: 0;
}}
QFrame#appHeader QLabel {{
    color: {t["header_text"]};
}}
QLabel#brandTitle {{
    font-size: 15px;
    font-weight: 700;
    color: {t["header_text"]};
}}
QLabel#brandSubtitle {{
    font-size: 11px;
    color: {t["header_muted"]};
}}
QFrame#userChip {{
    background: {t["header_chip"]};
    border-radius: 999px;
    padding: 4px 14px;
}}
QFrame#appHeader QPushButton#logoutBtn,
QFrame#appHeader QPushButton#themeToggle {{
    background: {t["header_chip"]};
    color: {t["header_text"]};
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
}}
QFrame#appHeader QPushButton#logoutBtn:hover,
QFrame#appHeader QPushButton#themeToggle:hover {{
    background: {t["header_chip_hover"]};
}}

/* ---------- Login (card) ---------- */
#loginCard {{
    background: {t["card"]};
    border: 1px solid {t["border"]};
    border-radius: 16px;
}}
#titleLabel {{
    font-size: 24px;
    font-weight: 700;
    color: {t["text"]};
}}
#subtitleLabel {{
    color: {t["text_muted"]};
    font-size: 13px;
}}
#fieldLabel {{
    font-weight: 600;
    color: {t["text"]};
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
    background: {t["muted_bg"]};
    color: {t["text"]};
    min-height: 42px;
    font-size: 14px;
}}
QPushButton#secondaryBtn:hover {{
    background: {t["alternate"]};
}}
QPushButton#resetBtn {{
    background: {t["muted_bg"]};
    color: {t["text"]};
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
    min-height: 22px;
}}
QPushButton#resetBtn:hover {{
    background: {t["alternate"]};
}}
QPushButton#revealBtn {{
    background: {t["accent"]};
    color: {t["on_accent"]};
    border-radius: 6px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#revealBtn:hover {{
    background: {t["accent_hover"]};
}}
QPushButton#smallBtn {{
    background: {t["muted_bg"]};
    color: {t["text"]};
    border-radius: 6px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton#smallBtn:hover {{
    background: {t["alternate"]};
}}
QPushButton#chooseBtn {{
    background: {t["primary"]};
    color: {t["on_primary"]};
    border-radius: 8px;
    padding: 5px 16px;
    font-size: 12px;
    font-weight: 600;
    min-height: 28px;
}}
QPushButton#chooseBtn:hover {{
    background: {t["primary_hover"]};
}}

/* ---------- Hero login (gambar Unsplash + scrim) ---------- */
#heroPanel {{
    background: #0d1117;
}}
#heroImage {{
    border-radius: 0;
}}
#loginScrim {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 rgba(9, 12, 22, 120),
        stop: 1 rgba(9, 12, 22, 215));
}}
#heroTitle {{
    color: #ffffff;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 0.5px;
}}
#heroSubtitle {{
    color: #cfd8ff;
    font-size: 14px;
    font-weight: 600;
}}
#heroTag {{
    color: #9aa7c7;
    font-size: 12px;
}}
QDialog#registerDialog {{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #eef1f8, stop: 1 #f7f8fc);
}}

/* ---------- Progress (busy) ---------- */
QProgressBar {{
    background: {t["muted_bg"]};
    border: 1px solid {t["border"]};
    border-radius: 5px;
    height: 8px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {t["primary"]};
    border-radius: 4px;
}}

/* ---------- Scrollbar ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {t["handle"]};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t["handle_hover"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


# ---------------------------------------------------------------------------
# API publik
# ---------------------------------------------------------------------------

def _palette(dark: bool) -> QPalette:
    t = _DARK if dark else _LIGHT
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(t["bg"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(t["card"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(t["muted_bg"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(t["primary"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(t["on_primary"]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(t["placeholder"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(t["card"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(t["text"]))
    return palette


def apply_theme(app: QApplication, dark: bool = False) -> None:
    """Terapkan tema global: Fusion + palet + QSS (terang/gelap)."""
    global _dark_mode, _cursor_filter
    _dark_mode = dark
    _register_font()
    app.setStyle("Fusion")
    app.setPalette(_palette(dark))
    app.setStyleSheet(_build_qss(_DARK if dark else _LIGHT))
    if _cursor_filter is None:
        _cursor_filter = _CursorPolishFilter(app)
        app.installEventFilter(_cursor_filter)


def is_dark() -> bool:
    return _dark_mode


def toggle_theme(app: QApplication) -> bool:
    """Balik mode gelap/terang; kembalikan state baru."""
    apply_theme(app, dark=not is_dark())
    return is_dark()


def make_theme_toggle_button(on_toggled: Optional[Callable[[], None]] = None):
    """Tombol toggle kecil; `on_toggled` dipanggil setelah ganti tema."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton

    btn = QPushButton("Mode Gelap" if not is_dark() else "Mode Terang")
    btn.setObjectName("themeToggle")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_click() -> None:
        toggle_theme(QApplication.instance())
        btn.setText("Mode Gelap" if not is_dark() else "Mode Terang")
        if on_toggled is not None:
            on_toggled()

    btn.clicked.connect(_on_click)
    return btn
