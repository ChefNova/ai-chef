"""Gemini vision client. This module performs the only networked model call."""

from __future__ import annotations

import base64
import json
import os
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pantry_extraction.pipeline import MissingApiKey
from pantry_extraction.schema import EXTRACTION_PROMPT, EXTRACTION_SCHEMA

API_ENV_VAR = "GEMINI_API_KEY"
DEFAULT_MODEL = "gemini-3.8-flash"
_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiReceiptModel:
    """ReceiptModel implementation. Construct it only when GEMINI_API_KEY is set."""

    def __init__(self, api_key: str, model: str | None = None, timeout: float = 30):
        if not api_key or not str(api_key).strip():
            raise MissingApiKey(API_ENV_VAR)
        self._api_key = str(api_key).strip()
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self._timeout = timeout

    def extract(self, image_bytes: bytes, mime_type: str) -> str:
        body = {
            "contents": [
                {
                    "parts": [
                        {"text": EXTRACTION_PROMPT},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "thinkingConfig": {"thinkingLevel": "low"},
                "responseFormat": {
                    "text": {
                        "mimeType": "APPLICATION_JSON",
                        "schema": EXTRACTION_SCHEMA,
                    }
                },
            },
        }
        # The key stays in a header so an error URL cannot carry it.
        request = Request(
            _ENDPOINT.format(model=self._model),
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise RuntimeError(_http_error_message(exc, self._api_key)) from exc
        return _response_text(payload)


def model_from_env() -> GeminiReceiptModel:
    """Return a live client, or raise MissingApiKey. Does not call the network."""
    api_key = os.environ.get(API_ENV_VAR, "").strip()
    if not api_key:
        raise MissingApiKey(API_ENV_VAR)
    return GeminiReceiptModel(api_key=api_key)


def _http_error_message(exc: HTTPError, api_key: str) -> str:
    """Status plus Gemini's message. Never include the key or the request URL."""
    detail = ""
    try:
        raw = exc.read()
    except Exception:
        raw = b""
    if raw:
        text = raw.decode("utf-8", errors="replace").strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        message = None
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict) and isinstance(error.get("message"), str):
                message = error["message"]
        detail = (message or text).strip()
    if not detail:
        reason = getattr(exc, "reason", None)
        detail = reason.strip() if isinstance(reason, str) and reason.strip() else "request rejected"
    detail = _redact_secret(detail, api_key)
    detail = " ".join(detail.split())
    if len(detail) > 240:
        detail = detail[:239].rstrip() + "…"
    return f"HTTP {exc.code}: {detail}"


def _redact_secret(text: str, api_key: str) -> str:
    if api_key:
        text = text.replace(api_key, "[redacted]")
    text = re.sub(r"(?i)([?&]key=)[^&\s\"']+", r"\1[redacted]", text)
    text = re.sub(r"AIza[0-9A-Za-z_\-]{10,}", "[redacted]", text)
    return text


def _response_text(payload: dict) -> str:
    try:
        parts = payload["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Gemini returned no candidate text") from exc
    texts = [
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and part.get("text") and not part.get("thought")
    ]
    if not texts:
        raise RuntimeError("Gemini returned no candidate text")
    return "\n".join(texts)
