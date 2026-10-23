# Recipe recommendation model

Recipe ranking calls Gemini once, then this app checks the JSON locally. The confirmed pantry, diet, maximum time, and avoid list are hard checks. A recipe the model labels as safe is still dropped when an ingredient breaks those checks. Pantry overlap, not a keyword score, sets Cook now, Almost ready, and Needs shopping.

## Model

`gemini-3.5-flash-lite` is the default (`RECIPE_MODEL`).

| Setting | Value |
|---|---|
| Endpoint | `generateContent` on `v1beta` |
| Thinking | `low` |
| Response | `responseFormat.text` with `mimeType` `APPLICATION_JSON` and the schema in `recipe_recommendation/schema.py` |
| Sampling | Gemini 3 defaults. Temperature is not sent. |
| Timeout | 30 seconds |
| Busy retry | 2 attempts, then `gemini-3.1-flash-lite` |
| Key | `x-goog-api-key` header. The saved receipt key or `GEMINI_API_KEY`. |

`GEMINI_RECIPE_MODEL` pins one model and skips the fallback. An empty pantry never calls Gemini.

## Why this model

The call is a short text prompt in and a short JSON list out. It does not read a receipt image.

- `gemini-3.5-flash-lite` is the high-throughput Flash-Lite model: about $0.30 per million input tokens and $2.50 per million output tokens. Its default thinking level is `minimal`. This app sets `low`, which that model supports, so the reply stays a structured list instead of a long trace.
- `gemini-3.8-flash` is stronger and slower. Introductory price through December 31, 2026 is about $0.75 / $3.75 per million input / output tokens, then about $1.50 / $7.50. Its default thinking level is `medium`. On this project it also returned HTTP 503 under load, and `gemini-3.6-flash` (about $1.50 / $7.50) did the same.
- `gemini-3.1-flash-lite` is the fallback. It is the older high-volume lite model, still listed for text and structured output, at about $0.25 / $1.50 per million tokens.

A ranking is one request. At roughly 800 input tokens and 900 output tokens, the lite price is about a quarter of a cent. That is an estimate from published token prices, not a measured bill. The wait is one request, capped at 30 seconds, plus a short retry only when Gemini returns 429, 500, or 503. This checkout did not time a live ranking for this note.

Receipt scanning still uses its own model chain, starting at `gemini-3.8-flash`. Ranking does not change that path.
