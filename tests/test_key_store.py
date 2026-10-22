"""Saved Gemini key stays on disk and is preferred over the environment."""

import os
import stat

from pantry_extraction.key_store import prefill_api_key, read_saved_api_key, save_api_key


def test_saved_key_prefills_ahead_of_the_environment(tmp_path):
    path = tmp_path / "gemini_api_key"
    save_api_key("saved-key", path)
    value, source = prefill_api_key(path, { "GEMINI_API_KEY": "env-key" })
    assert value == "saved-key"
    assert source == "saved"
    assert read_saved_api_key(path) == "saved-key"
    mode = stat.S_IMODE(path.stat().st_mode)
    assert mode == 0o600


def test_environment_prefills_only_when_nothing_is_saved(tmp_path):
    path = tmp_path / "missing"
    value, source = prefill_api_key(path, {"GEMINI_API_KEY": " env-key "})
    assert value == "env-key"
    assert source == "env"
    assert not path.exists()


def test_prefill_is_empty_when_nothing_is_stored(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    value, source = prefill_api_key(tmp_path / "missing", os.environ)
    assert value == ""
    assert source == "none"


def test_replacing_a_saved_key_overwrites_the_file(tmp_path):
    path = tmp_path / "nested" / "gemini_api_key"
    save_api_key("first", path)
    save_api_key("second", path)
    assert read_saved_api_key(path) == "second"
