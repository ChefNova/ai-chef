# Recipe recommendations

Recipes use Groq first when a Groq key is available, with Gemini as fallback on API errors, timeouts, empty content, or invalid recipe output. Either provider works on its own. A valid empty recipe list is respected and does not trigger fallback.

Keys come from the groceries tab, otherwise `GROQ_API_KEY` / `GEMINI_API_KEY`. Local development settings can go in `app/.env`; see `.env.example`.

| Provider | Recipe model | Response |
| --- | --- | --- |
| Groq (primary) | `openai/gpt-oss-120b`, configurable with `GROQ_RECIPE_MODEL` | JSON object mode with the `RecipeList` schema in the prompt |
| Gemini (fallback) | `gemini-3.5-flash-lite` | JSON with `RecipeList` response schema |

Groq recipes use a separate setting from the receipt extractor's `GROQ_MODEL`. Requests have a 20-second timeout and no automatic SDK retries. JSON object mode follows [Groq documentation](https://console.groq.com/docs/structured-outputs). Both providers pass through the same local recipe and ingredient consistency checks.

The confirmed pantry and constraints go to each attempted provider. An empty pantry or missing keys prevents requests. If every configured provider fails, the page shows an error and no replacement recipes. Successful fallback shows a notice. Recipe details show the successful provider and model.

Diet, maximum time, and avoid ingredients are local hard filters. Cook now, Almost ready, and Needs shopping reflect ingredient overlap, not verified quantity feasibility. Chat refinements filter or reorder existing suggestions; Refresh recipes requests a new set.

Receipt extraction is unchanged and retains its existing Groq-first, Gemini-fallback path.

The [evaluation report](../validation/recommendations/REPORT.md) records measured application checks, known failures, latency scope, model-selection evidence, and estimated costs. Reproduce it with `python -m validation.recommendations.evaluate --live`; live calls require environment keys and use synthetic pantries only.
