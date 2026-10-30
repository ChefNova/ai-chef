# Recipe recommendation model

Ranking asks Gemini for recipes, then this app checks the JSON against the confirmed pantry. Diet, maximum time, and the avoid list are hard filters. Cook now, Almost ready, and Needs shopping come from how many listed ingredients are already in the pantry. The match percent on each card is that overlap, not a keyword score.

Receipt extraction on this branch is unchanged: Groq is tried first when a Groq key is present, then Gemini. Recipe ranking does not use that path. It calls `get_gemini_client` in `app/receipt_extractor.py` and does not call Grok (xAI).

## Model

Recommendations call the same Gemini client with a different model: `gemini-3.5-flash-lite`.

| Setting | Value |
|---|---|
| Client | `app.receipt_extractor.get_gemini_client` |
| Key | The Gemini key typed on the receipt tab, otherwise `GEMINI_API_KEY` |
| Model | `gemini-3.5-flash-lite` |
| Response | `application/json` with the `RecipeList` schema |
| Sampling | Gemini 3 defaults. Temperature is not sent. Thinking level is `low` when the SDK exposes `ThinkingConfig`. |
| Call | One `generate_content` request. No image. |

An empty pantry or a missing key does not call the model. A bad JSON payload, or a recipe whose substitutions name an ingredient it does not list, shows an error and no recipes.

## Why Gemini Flash-Lite, not Grok (xAI)

Grok (xAI) would need its own API key. It does not read the receipt image, so it would not help that path.

Recipe ranking stays on Gemini so the cook uses the key they already entered. Flash-Lite fits this call: a short pantry list in, a short JSON list out.

`gemini-3.8-flash` stays the receipt model. It is the stronger default in the extractor, with heavier default thinking and a higher token price (about $0.75 / $3.75 per million input / output tokens through December 31, 2026, then about $1.50 / $7.50). It has also returned HTTP 503 when demand spikes. `gemini-3.5-flash-lite` is the high-throughput model at about $0.30 / $2.50 per million tokens. A ranking of roughly 800 input tokens and 900 output tokens is about a quarter of a cent at that list price. That is an estimate from published prices, not a measured bill.

The wait is one text request. This path does not retry for 15 seconds and does not switch to Grok (xAI). If Gemini fails, the page says so and does not invent recipes.
