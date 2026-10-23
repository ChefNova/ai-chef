"""Gemini recipe client. This module performs the only networked recommendation call."""

from __future__ import annotations

import json
import os
import re
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from pantry_extraction.pipeline import MissingApiKey
from recipe_recommendation.schema import (
    FALLBACK_MODELS,
    RECIPE_MODEL,
    RECIPE_SCHEMA,
    THINKING_LEVEL,
    TIMEOUT_SECONDS,
)

_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
_BUSY_STATUS = {429, 500, 503}
_ATTEMPTS = 2
_BACKOFF_SECONDS = (0.5,)


class GeminiRecipeModel:
    """Text-only generateContent client. Construct it with a key the UI already holds."""

    def __init__(self, api_key: str, model: str | None = None, timeout: float = TIMEOUT_SECONDS):
        if not api_key or not str(api_key).strip():
            raise MissingApiKey("GEMINI_API_KEY")
        self._api_key = str(api_key).strip()
        chosen = (model or os.environ.get("GEMINI_RECIPE_MODEL") or "").strip()
        self._model = chosen or RECIPE_MODEL
        self._allow_fallback = not chosen
        self._timeout = timeout
        self.model_used: str | None = None

    def recommend(self, prompt: str) -> str:
        models = [self._model]
        if self._allow_fallback:
            for name in FALLBACK_MODELS:
                if name not in models:
                    models.append(name)
        last_message = "HTTP 503: Gemini is busy."
        for model_name in models:
            try:
                text = self._recommend_model(prompt, model_name)
            except _TryNext as exc:
                last_message = str(exc)
                continue
            self.model_used = model_name
            return text
        suffix = " Tried " + " and ".join(models) + "."
        if len(last_message) + len(suffix) > 240:
            last_message = last_message[: 239 - len(suffix)].rstrip() + "…"
        raise RuntimeError(last_message + suffix)

    def _recommend_model(self, prompt: str, model_name: str) -> str:
        for attempt in range(_ATTEMPTS):
            try:
                return self._once(prompt, model_name)
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

    def _once(self, prompt: str, model_name: str) -> str:
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "thinkingConfig": {"thinkingLevel": THINKING_LEVEL},
                "responseFormat": {
                    "text": {
                        "mimeType": "APPLICATION_JSON",
                        "schema": RECIPE_SCHEMA,
                    }
                },
            },
        }
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


def _http_error_message(exc: HTTPError, api_key: str) -> str:
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
        detail = "request rejected"
    if api_key:
        detail = detail.replace(api_key, "[redacted]")
    detail = re.sub(r"(?i)([?&]key=)[^&\s\"']+", r"\1[redacted]", detail)
    detail = re.sub(r"AIza[0-9A-Za-z_\-]{10,}", "[redacted]", detail)
    detail = " ".join(detail.split())
    if len(detail) > 240:
        detail = detail[:239].rstrip() + "…"
    return f"HTTP {exc.code}: {detail}"


def _response_text(payload: dict) -> str:
    try:
        parts = payload["candidates"][0]["content"]["parts"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Gemini returned no recipe text") from exc
    texts = [
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and part.get("text") and not part.get("thought")
    ]
    if not texts:
        raise RuntimeError("Gemini returned no recipe text")
    return "\n".join(texts)
