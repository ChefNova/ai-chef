"""
Unit tests for receipt_extractor.py

Tests focus on the data-transformation logic that does NOT require
a live Tesseract install or LLM API call. OCR and LLM calls are mocked.
"""

from unittest.mock import patch

import pytest

from app.schemas import GroceryItem, ReceiptExtraction


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_OCR_TEXT = """
WHOLE FOODS MARKET
123 Main St, Springfield

Organic Spinach 5oz    2.99
Large Eggs 12ct        4.49
Whole Milk 1gal        3.79
---
SUBTOTAL               11.27
TAX                     0.90
TOTAL                  12.17
VISA **** 1234
"""

SAMPLE_EXTRACTION_JSON = {
    "items": [
        {"name": "Organic Spinach", "quantity": 1, "unit": "5oz bag", "confidence": 0.95, "source_text": "Organic Spinach 5oz    2.99"},
        {"name": "Large Eggs", "quantity": 12, "unit": "unit", "confidence": 0.97, "source_text": "Large Eggs 12ct        4.49"},
        {"name": "Whole Milk", "quantity": 1, "unit": "gal", "confidence": 0.98, "source_text": "Whole Milk 1gal        3.79"},
    ]
}


# ---------------------------------------------------------------------------
# Schema validation tests (no mocking needed)
# ---------------------------------------------------------------------------

def test_grocery_item_valid():
    item = GroceryItem(name="Spinach", quantity=1, unit="bag", confidence=0.95, source_text="Spinach 1 bag")
    assert item.name == "Spinach"
    assert item.confidence == 0.95


def test_grocery_item_rejects_negative_confidence():
    with pytest.raises(Exception):
        GroceryItem(name="Spinach", quantity=1, unit="bag", confidence=-0.1, source_text="Spinach")


def test_receipt_extraction_filters_non_food_fields():
    """Non-food fields (subtotal, tax, total) must not appear in extracted items."""
    result = ReceiptExtraction(**SAMPLE_EXTRACTION_JSON)
    names = [item.name.lower() for item in result.items]
    for forbidden in ("subtotal", "tax", "total", "visa"):
        assert forbidden not in names, f"Non-food field '{forbidden}' leaked into extraction"


def test_receipt_extraction_item_count():
    result = ReceiptExtraction(**SAMPLE_EXTRACTION_JSON)
    assert len(result.items) == 3


# ---------------------------------------------------------------------------
# Extractor integration test (mocked OCR + LLM)
# ---------------------------------------------------------------------------

@patch("app.receipt_extractor.extract_text_with_ocr", return_value=SAMPLE_OCR_TEXT)
@patch("app.receipt_extractor.extract_with_groq", return_value=ReceiptExtraction(**SAMPLE_EXTRACTION_JSON))
def test_extract_receipt_returns_validated_items(mock_llm, mock_ocr):
    from app.receipt_extractor import extract_receipt

    result = extract_receipt("test_receipt.jpg", groq_api_key="test-key")
    assert isinstance(result.extraction, ReceiptExtraction)
    assert len(result.extraction.items) == 3
    assert result.extraction.items[0].name == "Organic Spinach"
    mock_ocr.assert_called_once_with("test_receipt.jpg")
    mock_llm.assert_called_once()
    payload = mock_llm.call_args.args[0]
    assert "Organic Spinach" in payload
    assert all(text not in payload for text in ("VISA", "SUBTOTAL", "Main St"))


@patch("app.receipt_extractor.extract_text_with_ocr", return_value="")
@patch("app.receipt_extractor.extract_with_groq")
def test_extract_receipt_empty_ocr(mock_llm, mock_ocr):
    from app.receipt_extractor import extract_receipt

    result = extract_receipt("blank.jpg", groq_api_key="test-key")
    assert result.source == "manual_review"
    assert result.extraction is None
    mock_llm.assert_not_called()
