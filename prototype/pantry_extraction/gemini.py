"""Gemini vision client. This module performs the only networked model call."""

from __future__ import annotations

import base64
import json
import os
from urllib.request import Request, urlopen

from pantry_extraction.pipeline import MissingApiKey
from pantry_extraction.schema import EXTRACTION_PROMPT, EXTRACTION_SCHEMA

API_ENV_VAR = "GEMINI_API_KEY"
DEFAULT_MODEL = "gemini-2.5-flash"
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
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseSchema": EXTRACTION_SCHEMA,
            },
        }
        url = _ENDPOINT.format(model=self._model) + f"?key={self._api_key}"
        request = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self._timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _response_text(payload)


def model_from_env() -> GeminiReceiptModel:
    """Return a live client, or raise MissingApiKey. Does not call the network."""
    api_key = os.environ.get(API_ENV_VAR, "").strip()
    if not api_key:
        raise MissingApiKey(API_ENV_VAR)
    return GeminiReceiptModel(api_key=api_key)


def _response_text(payload: dict) -> str:
    try:
        parts = payload["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Gemini returned no candidate text") from exc
    texts = [part.get("text", "") for part in parts if isinstance(part, dict) and part.get("text")]
    if not texts:
        raise RuntimeError("Gemini returned no candidate text")
    return "\n".join(texts)
