"""Uji UI offscreen: ImageTab (stego) & AssetTab (blockchain)."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import json

import cv2
import numpy as np
import pytest

from app.ui.asset_tab import AssetTab
from app.ui.image_tab import ImageTab

KEY = b"pass-stego"


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app


def test_image_tab_embed_extract(qapp, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    cover_path = tmp_path / "cover.png"
    rng = np.random.default_rng(3)
    cv2.imwrite(str(cover_path), rng.integers(0, 256, (120, 120, 3), dtype=np.uint8))
    stego_path = tmp_path / "stego.png"

    tab = ImageTab()
    embed, extract = tab.embed_panel, tab.extract_panel

    # --- Sisip ---
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(cover_path), ""))
    embed.choose_btn.click()
    assert embed._image is not None
    assert not embed.preview_label.pixmap().isNull()

    embed.message_edit.setPlainText("Pesan rahasia stego")
    embed.password_edit.setText(KEY.decode())
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(stego_path), ""))
    embed.action_btn.click()
    assert stego_path.exists()

    # --- Ekstrak ---
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(stego_path), ""))
    extract.choose_btn.click()
    extract.password_edit.setText(KEY.decode())
    extract.action_btn.click()
    assert extract.message_edit.toPlainText() == "Pesan rahasia stego"


def test_asset_tab_add_and_verify(qapp, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    tab = AssetTab(difficulty=3)
    tab.name_edit.setText("Laptop")
    tab.hash_edit.setText("abc123")
    tab.owner_edit.setText("Budi")
    tab.add_btn.click()
    assert tab.table.rowCount() == 2  # genesis + 1
    tab.verify_btn.click()
    assert "VALID" in tab.status_label.text()

    chain_path = tmp_path / "chain.json"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(chain_path), ""))
    tab.save_btn.click()
    assert chain_path.exists()
    payload = json.loads(chain_path.read_text(encoding="utf-8"))
    assert payload["difficulty"] == 3

    tab2 = AssetTab(difficulty=3)
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(chain_path), ""))
    tab2.load_btn.click()
    assert tab2.table.rowCount() == 2
