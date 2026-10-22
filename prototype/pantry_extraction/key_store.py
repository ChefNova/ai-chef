"""Local Gemini key prefill. The saved file is gitignored and never logged."""

from __future__ import annotations

import os
from pathlib import Path

from pantry_extraction.gemini import API_ENV_VAR

def default_key_path() -> Path:
    return Path(__file__).resolve().parents[1] / ".chefnova" / "gemini_api_key"


def read_saved_api_key(path: Path | None = None) -> str:
    target = path or default_key_path()
    try:
        text = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except OSError:
        return ""
    return text.strip()


def prefill_api_key(path: Path | None = None, environ: dict | None = None) -> tuple[str, str]:
    """Return (key, source). Source is saved, env, or none. Does not call the network."""
    saved = read_saved_api_key(path)
    if saved:
        return saved, "saved"
    env = (environ if environ is not None else os.environ).get(API_ENV_VAR, "")
    env = str(env).strip()
    if env:
        return env, "env"
    return "", "none"


def save_api_key(api_key: str, path: Path | None = None) -> None:
    """Write the key to a local file. Caller must not log the value."""
    key = str(api_key).strip()
    if not key:
        raise ValueError("refusing to save an empty Gemini API key")
    target = path or default_key_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, key.encode("utf-8"))
    finally:
        os.close(fd)
    os.chmod(target, 0o600)
