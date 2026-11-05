"""OCR executable discovery without a native Tesseract installation."""

import pytest

from app import receipt_extractor as extractor


def test_custom_ocr_executable_is_used(monkeypatch):
    monkeypatch.setenv("TESSERACT_CMD", "C:/custom/tesseract.exe")
    monkeypatch.setattr(extractor.shutil, "which", lambda path: path if path == "C:/custom/tesseract.exe" else None)
    monkeypatch.setattr(extractor.pytesseract.pytesseract, "tesseract_cmd", "tesseract")
    extractor.configure_tesseract()
    assert extractor.pytesseract.pytesseract.tesseract_cmd == "C:/custom/tesseract.exe"


def test_missing_ocr_engine_explains_native_dependency(monkeypatch):
    monkeypatch.delenv("TESSERACT_CMD", raising=False)
    monkeypatch.setattr(extractor.shutil, "which", lambda path: None)
    with pytest.raises(RuntimeError, match="pip only installs its Python wrapper"):
        extractor.configure_tesseract()
