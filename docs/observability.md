# ChefNova — Observability Strategy

## Overview

ChefNova logs latency, token cost, and errors for every LLM call and OCR operation. All telemetry is written to stdout / stderr in a structured format and optionally to a rotating local log file. No external observability service is required for local development.

---

## What is logged

### LLM calls (`recipe_recommendations.py`)

Each recipe recommendation cycle makes up to three LLM calls, each logged separately:

1. **Generation** — Groq (primary) or Gemini (fallback) produces the recipe list.
2. **Ranking** — Gemini Flash-Lite ranks the generated recipes by protein, time, and pantry coverage.

Each call to Groq or Gemini emits a log entry containing:

| Field | Description |
|-------|-------------|
| `provider` | `groq` or `gemini` |
| `model` | Model identifier (e.g. `qwen/qwen3.8-27b`) |
| `latency_ms` | Round-trip time for the API call |
| `prompt_tokens` | Tokens consumed by the prompt |
| `completion_tokens` | Tokens consumed by the completion |
| `total_tokens` | Sum of prompt + completion tokens |
| `estimated_cost_usd` | Estimated cost based on published per-token pricing |
| `status` | `success` \| `fallback` \| `error` |
| `error_message` | Populated on failure |

**Example log line (JSON):**

```json
{
  "ts": "2026-11-04T22:30:01Z",
  "event": "llm_call",
  "provider": "groq",
  "model": "qwen/qwen3.8-27b",
  "latency_ms": 342,
  "prompt_tokens": 418,
  "completion_tokens": 611,
  "total_tokens": 1029,
  "estimated_cost_usd": 0.00041,
  "status": "success"
}
```

### OCR calls (`receipt_extractor.py`)

| Field | Description |
|-------|-------------|
| `image_name` | Filename of the uploaded receipt (no PII path) |
| `ocr_latency_ms` | Tesseract processing time |
| `char_count` | Character count of raw OCR output |
| `confidence_mean` | Mean Tesseract confidence across all words |

### Errors

All exceptions are caught and logged at `ERROR` level with:
- Exception type and message
- Stack trace (truncated to 10 frames in production)
- Request context (provider, model, operation)

---

## Log levels

| Level | Used for |
|-------|---------|
| `DEBUG` | Full prompt text, raw LLM responses (enable via `CHEFNOVA_DEBUG_LOGGING=true`) |
| `INFO` | Every LLM call summary, OCR summary |
| `WARNING` | Fallback triggered, low-confidence items, partial OCR |
| `ERROR` | API failures, Pydantic validation failures, unhandled exceptions |

---

## How to enable debug logging

Set in your `.env`:

```
CHEFNOVA_DEBUG_LOGGING=true
LOG_LEVEL=DEBUG
```

This prints full prompt and completion text to stdout. **Do not enable in production or shared environments** — prompts may contain user pantry data.

---

## Viewing live telemetry

While the app is running, pipe stdout to a pretty-printer:

```bash
streamlit run ChefNova_app_UI.py 2>&1 | python -m json.tool
```

---

## Metrics tracked in `validation/`

The `validation/` directory contains evaluation scripts (`evaluate.py`) that run a batch of test cases and produce:

- `results.json` — per-case accuracy, latency, token cost
- `live-results.json` — results from live API calls (for regression tracking)
- `REPORT.md` — human-readable summary with pass/fail counts and cost totals

Run:

```bash
python validation/recommendations/evaluate.py
```

---

## Debugging a failed recommendation

1. Set `CHEFNOVA_DEBUG_LOGGING=true`.
2. Reproduce the failure in the UI.
3. Look for `"status": "error"` or `"status": "fallback"` in the log.
4. The `error_message` field shows the raw API error.
5. If the LLM returned malformed JSON, the `DEBUG` log shows the raw completion text.
