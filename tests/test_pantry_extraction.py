"""Pantry extraction tests. Model responses are fixtures. No network."""

import io
import json
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from pantry_extraction.gemini import DEFAULT_MODEL, FALLBACK_MODEL, GeminiReceiptModel
from pantry_extraction.pipeline import (
    MissingApiKey,
    confirm_review_into_inventory,
    extract_receipt,
    parse_model_output,
)
from pantry_extraction.schema import EXTRACTION_PROMPT, EXTRACTION_SCHEMA
from pantry_extraction.validate import validate_item


class FakeModel:
    def __init__(self, raw):
        self.raw = raw
        self.calls = []

    def extract(self, image_bytes, mime_type):
        self.calls.append((image_bytes, mime_type))
        if isinstance(self.raw, Exception):
            raise self.raw
        return self.raw


def _payload(readable, items, failure_reason=None):
    return json.dumps(
        {"readable": readable, "failure_reason": failure_reason, "items": items}
    )


def test_unreadable_receipt_returns_failure_and_drops_invented_items():
    raw = _payload(
        False,
        [{"name": "Invented Rice", "quantity": 2, "unit": "lb", "missing_fields": []}],
        "Image is too blurry to read.",
    )
    result = parse_model_output(raw)
    assert result.ok is False
    assert result.items == []
    assert "blurry" in result.failure_reason


def test_partial_read_keeps_readable_items_and_marks_gaps():
    raw = _payload(
        True,
        [
            {"name": "Milk", "quantity": 1, "unit": "gallon", "missing_fields": []},
            {"name": "Bananas", "quantity": None, "unit": None, "missing_fields": ["quantity", "unit"]},
        ],
    )
    result = parse_model_output(raw)
    assert result.ok is True
    assert len(result.items) == 2
    assert result.items[0].ok
    assert result.items[0].name == "Milk"
    assert result.items[1].ok is False
    assert result.items[1].missing_fields == ["quantity", "unit"]
    assert "still need" in result.notice


def test_invalid_json_and_non_object_extract_nothing():
    broken = parse_model_output("not json")
    assert broken.ok is False and broken.items == []
    listed = parse_model_output(json.dumps([{"name": "Rice"}]))
    assert listed.ok is False and listed.items == []


def test_missing_readable_flag_extracts_nothing():
    result = parse_model_output(json.dumps({"items": []}))
    assert result.ok is False
    assert result.items == []


def test_validate_rejects_blank_name_bad_quantity_and_unknown_unit():
    blank = validate_item(name="  ", quantity=1, unit="lb")
    assert "name" in blank.missing_fields
    bad_qty = validate_item(name="Rice", quantity=-2, unit="lb")
    assert any("quantity" in error for error in bad_qty.errors)
    text_qty = validate_item(name="Rice", quantity="two", unit="lb")
    assert text_qty.ok is False
    money = validate_item(name="Rice", quantity=4.29, unit="$")
    assert any("unit" in error for error in money.errors)
    good = validate_item(name=" whole milk ", quantity="1", unit="gallons")
    assert good.ok
    assert good.unit == "gallon"
    assert good.quantity == 1


def test_confirm_does_not_write_inventory_until_every_row_is_valid():
    inventory = [{"Ingredient": "Rice", "Quantity": 1, "Unit": "lb"}]
    rejected = confirm_review_into_inventory(
        inventory,
        [
            {"Ingredient": "Milk", "Quantity": 1, "Unit": "gallon"},
            {"Ingredient": "Bananas", "Quantity": None, "Unit": ""},
        ],
    )
    assert rejected.accepted is False
    assert rejected.inventory == inventory
    assert inventory == [{"Ingredient": "Rice", "Quantity": 1, "Unit": "lb"}]

    accepted = confirm_review_into_inventory(
        inventory,
        [{"Ingredient": "Rice", "Quantity": 2, "Unit": "lbs"}],
    )
    assert accepted.accepted is True
    assert accepted.inventory[0]["Quantity"] == 3
    assert accepted.inventory[0]["Unit"] == "lb"
    # The original list is unchanged until the caller saves the returned one.
    assert inventory[0]["Quantity"] == 1


def test_confirm_keeps_different_units_separate():
    outcome = confirm_review_into_inventory(
        [{"Ingredient": "Rice", "Quantity": 1, "Unit": "lb"}],
        [{"Ingredient": "Rice", "Quantity": 2, "Unit": "cups"}],
    )
    assert outcome.accepted
    assert len(outcome.inventory) == 2


def test_empty_or_unsupported_file_does_not_call_the_model():
    model = FakeModel(_payload(True, [{"name": "Rice", "quantity": 1, "unit": "lb", "missing_fields": []}]))
    empty = extract_receipt(b"", "image/png", model)
    weird = extract_receipt(b"abc", "text/plain", model)
    assert empty.ok is False and empty.items == []
    assert weird.ok is False and weird.items == []
    assert model.calls == []


def test_model_exception_extracts_nothing():
    model = FakeModel(URLError("blocked"))
    result = extract_receipt(b"png", "image/png", model)
    assert result.ok is False
    assert result.items == []
    assert "URLError" in result.failure_reason


def test_successful_mock_extraction_does_not_touch_inventory():
    model = FakeModel(
        _payload(True, [{"name": "Chickpeas", "quantity": 2, "unit": "cans", "missing_fields": []}])
    )
    result = extract_receipt(b"fake-image", "image/jpeg", model)
    assert result.ok
    assert result.items[0].name == "Chickpeas"
    assert model.calls == [(b"fake-image", "image/jpeg")]


def test_missing_api_key_does_not_build_a_client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from pantry_extraction.gemini import model_from_env

    with pytest.raises(MissingApiKey):
        model_from_env()


def test_gemini_request_sends_prompt_and_schema_without_opening_a_real_socket(monkeypatch):
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    captured = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            body = {
                "readable": True,
                "failure_reason": None,
                "items": [{"name": "Spinach", "quantity": 1, "unit": "bag", "missing_fields": []}],
            }
            return json.dumps(
                {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"thought": True, "text": "checking the receipt"},
                                    {"text": json.dumps(body)},
                                ]
                            }
                        }
                    ]
                }
            ).encode()

    def _urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        captured["headers"] = {key.lower(): value for key, value in request.header_items()}
        captured["timeout"] = timeout
        return _Response()

    with patch("pantry_extraction.gemini.urlopen", _urlopen):
        model = GeminiReceiptModel(api_key="test-key-not-real")
        raw = model.extract(b"\x89PNG", "image/png")

    parsed = parse_model_output(raw)
    assert parsed.ok and parsed.items[0].name == "Spinach"
    assert f"/models/{DEFAULT_MODEL}:generateContent" in captured["url"]
    assert DEFAULT_MODEL == "gemini-3.8-flash"
    assert captured["body"]["contents"][0]["parts"][0]["text"] == EXTRACTION_PROMPT
    config = captured["body"]["generationConfig"]
    assert config["responseFormat"]["text"]["schema"] == EXTRACTION_SCHEMA
    assert config["responseFormat"]["text"]["mimeType"] == "APPLICATION_JSON"
    assert config["thinkingConfig"]["thinkingLevel"] == "low"
    assert "temperature" not in config
    assert "responseSchema" not in config
    assert "additionalProperties" not in json.dumps(config["responseFormat"]["text"]["schema"])
    assert captured["headers"]["x-goog-api-key"] == "test-key-not-real"
    assert "test-key-not-real" not in captured["url"]
    assert "test-key-not-real" not in json.dumps(captured["body"])
    image = captured["body"]["contents"][0]["parts"][1]["inlineData"]
    assert image["mimeType"] == "image/png"
    assert "inline_data" not in captured["body"]["contents"][0]["parts"][1]


def test_gemini_http_error_reports_status_without_the_api_key():
    secret = "test-key-not-real"

    def _urlopen(request, timeout):
        body = {
            "error": {
                "code": 400,
                "message": f"Invalid JSON payload received. Request URL had key={secret}",
                "status": "INVALID_ARGUMENT",
            }
        }
        raise HTTPError(
            request.full_url + "?key=" + secret,
            400,
            "Bad Request",
            hdrs=None,
            fp=io.BytesIO(json.dumps(body).encode()),
        )

    with patch("pantry_extraction.gemini.urlopen", _urlopen):
        model = GeminiReceiptModel(api_key=secret, model="gemini-3.8-flash")
        result = extract_receipt(b"\x89PNG", "image/png", model)

    assert result.ok is False
    assert result.items == []
    assert result.failure_reason is not None
    assert "HTTP 400" in result.failure_reason
    assert "Invalid JSON payload" in result.failure_reason
    assert secret not in result.failure_reason
    assert "key=[redacted]" in result.failure_reason


def test_gemini_client_refuses_a_blank_key():
    with pytest.raises(MissingApiKey):
        GeminiReceiptModel(api_key="  ")


def _http_error(request, code, message):
    body = {"error": {"code": code, "message": message, "status": "UNAVAILABLE"}}
    return HTTPError(
        request.full_url,
        code,
        "error",
        hdrs=None,
        fp=io.BytesIO(json.dumps(body).encode()),
    )


def _ok_response():
    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            body = {
                "readable": True,
                "failure_reason": None,
                "items": [{"name": "Kale", "quantity": 1, "unit": "bunch", "missing_fields": []}],
            }
            return json.dumps(
                {"candidates": [{"content": {"parts": [{"text": json.dumps(body)}]}}]}
            ).encode()

    return _Response()


def test_gemini_retries_a_busy_model_then_reads_the_receipt():
    calls = []

    def _urlopen(request, timeout):
        calls.append(request.full_url)
        if len(calls) < 3:
            raise _http_error(request, 503, "This model is currently experiencing high demand.")
        return _ok_response()

    with patch("pantry_extraction.gemini.urlopen", _urlopen), patch("pantry_extraction.gemini.time.sleep"):
        model = GeminiReceiptModel(api_key="test-key-not-real")
        raw = model.extract(b"\x89PNG", "image/png")

    parsed = parse_model_output(raw)
    assert parsed.ok and parsed.items[0].name == "Kale"
    assert len(calls) == 3
    assert all(DEFAULT_MODEL in url for url in calls)
    assert FALLBACK_MODEL not in "".join(calls)
    assert model.model_used == DEFAULT_MODEL


def test_gemini_falls_back_when_the_default_model_stays_busy():
    calls = []

    def _urlopen(request, timeout):
        calls.append(request.full_url)
        if DEFAULT_MODEL in request.full_url:
            raise _http_error(request, 503, "This model is currently experiencing high demand.")
        return _ok_response()

    with patch("pantry_extraction.gemini.urlopen", _urlopen), patch("pantry_extraction.gemini.time.sleep"):
        model = GeminiReceiptModel(api_key="test-key-not-real")
        result = extract_receipt(b"\x89PNG", "image/png", model)

    assert result.ok and result.items[0].name == "Kale"
    assert sum(DEFAULT_MODEL in url for url in calls) == 3
    assert sum(FALLBACK_MODEL in url for url in calls) == 1
    assert model.model_used == FALLBACK_MODEL


def test_gemini_does_not_retry_a_rejected_request():
    calls = []

    def _urlopen(request, timeout):
        calls.append(request.full_url)
        raise _http_error(request, 400, "Invalid JSON payload.")

    with patch("pantry_extraction.gemini.urlopen", _urlopen), patch("pantry_extraction.gemini.time.sleep"):
        model = GeminiReceiptModel(api_key="test-key-not-real")
        result = extract_receipt(b"\x89PNG", "image/png", model)

    assert result.ok is False and result.items == []
    assert len(calls) == 1
    assert "HTTP 400" in result.failure_reason
    assert FALLBACK_MODEL not in result.failure_reason


def test_gemini_reports_both_models_when_they_are_busy():
    def _urlopen(request, timeout):
        raise _http_error(request, 503, "This model is currently experiencing high demand.")

    with patch("pantry_extraction.gemini.urlopen", _urlopen), patch("pantry_extraction.gemini.time.sleep"):
        model = GeminiReceiptModel(api_key="test-key-not-real")
        result = extract_receipt(b"\x89PNG", "image/png", model)

    assert result.ok is False and result.items == []
    assert "HTTP 503" in result.failure_reason
    assert "high demand" in result.failure_reason
    assert DEFAULT_MODEL in result.failure_reason
    assert FALLBACK_MODEL in result.failure_reason
    assert "test-key-not-real" not in result.failure_reason


def test_pinned_model_does_not_fall_back_when_busy(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
    calls = []

    def _urlopen(request, timeout):
        calls.append(request.full_url)
        raise _http_error(request, 503, "This model is currently experiencing high demand.")

    with patch("pantry_extraction.gemini.urlopen", _urlopen), patch("pantry_extraction.gemini.time.sleep"):
        model = GeminiReceiptModel(api_key="test-key-not-real")
        result = extract_receipt(b"\x89PNG", "image/png", model)

    assert result.ok is False and result.items == []
    assert len(calls) == 3
    assert all("gemini-3.1-pro-preview" in url for url in calls)
    assert FALLBACK_MODEL not in result.failure_reason
