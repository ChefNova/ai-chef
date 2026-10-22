"""Gemini vision client. This module performs the only networked model call."""

from __future__ import annotations

import base64
import json
import os
import re
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pantry_extraction.pipeline import MissingApiKey
from pantry_extraction.schema import EXTRACTION_PROMPT, EXTRACTION_SCHEMA

API_ENV_VAR = "GEMINI_API_KEY"
DEFAULT_MODEL = "gemini-3.8-flash"
# Flash-Lite models are the high-throughput path when Flash is out of capacity.
FALLBACK_MODELS = (
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
)
_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_BUSY_STATUS = {429, 500, 503}
_ATTEMPTS = 2
_BACKOFF_SECONDS = (0.5,)


class GeminiReceiptModel:
    """ReceiptModel implementation. Construct it only when GEMINI_API_KEY is set."""

    def __init__(self, api_key: str, model: str | None = None, timeout: float = 30):
        if not api_key or not str(api_key).strip():
            raise MissingApiKey(API_ENV_VAR)
        self._api_key = str(api_key).strip()
        chosen = (model or os.environ.get("GEMINI_MODEL") or "").strip()
        self._model = chosen or DEFAULT_MODEL
        # A pinned model stays pinned. The default model can move on when Gemini is busy.
        self._allow_fallback = not chosen or chosen == DEFAULT_MODEL
        self._timeout = timeout
        self.model_used: str | None = None

    def _models(self) -> list[str]:
        if not self._allow_fallback:
            return [self._model]
        models: list[str] = []
        for name in (self._model, *FALLBACK_MODELS):
            if name not in models:
                models.append(name)
        return models

    def extract(self, image_bytes: bytes, mime_type: str) -> str:
        models = self._models()
        last_message = "HTTP 503: Gemini is busy."
        for model_name in models:
            try:
                text = self._extract_model(image_bytes, mime_type, model_name)
            except _TryNext as exc:
                last_message = str(exc)
                continue
            self.model_used = model_name
            return text
        suffix = _tried_phrase(models)
        if len(last_message) + len(suffix) > 240:
            last_message = last_message[: 239 - len(suffix)].rstrip() + "…"
        raise RuntimeError(last_message + suffix)

    def _extract_model(self, image_bytes: bytes, mime_type: str, model_name: str) -> str:
        for attempt in range(_ATTEMPTS):
            try:
                return self._extract_once(image_bytes, mime_type, model_name)
            except HTTPError as exc:
                message = _http_error_message(exc, self._api_key)
                if exc.code == 404:
                    raise _TryNext(message) from exc
                if exc.code not in _BUSY_STATUS:
                    raise RuntimeError(message) from exc
                if attempt == _ATTEMPTS - 1:
                    raise _TryNext(message) from exc
                time.sleep(_BACKOFF_SECONDS[min(attempt, len(_BACKOFF_SECONDS) - 1)])
        raise _TryNext("HTTP 503: Gemini is busy.")

    def _extract_once(self, image_bytes: bytes, mime_type: str, model_name: str) -> str:
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
            _ENDPOINT.format(model=model_name),
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            method="POST",
        )
        with urlopen(request, timeout=self._timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _response_text(payload)


class _TryNext(Exception):
    """This model is busy or gone. Another model may answer."""


def _tried_phrase(models: list[str]) -> str:
    if len(models) == 1:
        return f" Tried {models[0]}."
    if len(models) == 2:
        return f" Tried {models[0]} and {models[1]}."
    return f" Tried {', '.join(models[:-1])}, and {models[-1]}."


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
