# ChefNova observability

## Recipe requests in the app

Groq generates recipe candidates when configured. Gemini can generate candidates if Groq fails or returns invalid output. A request can therefore attempt both providers. Once ChefNova has a valid response, Python filters and ranks candidates locally using `rank_recipes()`. Ranking and reordering the existing results do not call a provider.

At INFO level, the [recipe module](../app/recipe_recommendations.py) emits provider, outcome, and elapsed milliseconds for attempts that return, fail, or produce invalid output. Successful attempts also include whether fallback was used. The recipe UI can show a fallback notice or a failure message, and recipe details show the successful provider and model.

The recipe clients can pass token usage to a caller through a callback. The benchmark uses that callback. The normal Streamlit recommendation flow does not emit per-request token or cost totals. Receipt extraction prints progress and provider outcomes. Typed and voice grocery structuring track their most recent elapsed time in Streamlit session state.

## Benchmark measurements

Run the local benchmark from the repository root:

```bash
python -m validation.recommendations.evaluate
```

With provider credentials configured, add `--live` to run real API calls using synthetic pantry inputs. The runner tests providers independently and records request latency, parse outcomes, result counts, reported token usage, and estimated list cost where usage and rates are available. The offline portion measures local processing and excludes OCR, UI rendering, and network time.

- [Offline results](../validation/recommendations/results.json)
- [Live provider results](../validation/recommendations/live-results.json)
- [Evaluation report](../validation/recommendations/REPORT.md)
- [Live walkthroughs, including automatic fallback](use-cases.md#live-walkthrough-results)

For a failed recommendation, start with the UI message, then check the provider outcome in the recipe logs when INFO logging is enabled. Use the benchmark for controlled comparisons of latency and token cost.
