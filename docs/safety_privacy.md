# ChefNova safety and privacy

ChefNova uses external model providers to structure grocery inputs and generate recipes. The app checks receipt evidence before presenting extracted items for review and checks recipe output before displaying recommendations.

## 1. Receipt PII sanitization

- Streamlit writes the uploaded image to a temporary local file so Tesseract can read it. The app attempts to delete the file when processing ends.
- Tesseract runs locally. Before calling Groq or Gemini, ChefNova keeps likely grocery lines and filters recognizable sensitive data such as addresses, phone numbers, emails, payment lines, and loyalty identifiers. The receipt path sends the filtered text to the provider.
- If filtering leaves no usable lines, the app offers manual entry without calling a provider. The filter is pattern-based. It can miss unfamiliar formats or drop valid content, such as a product name split from its price or weight by OCR.

The live synthetic-receipt walkthrough retained all three grocery lines and removed the synthetic loyalty ID. Tesseract misread one price. The [receipt pipeline](../app/receipt_extractor.py), [guardrail tests](../tests/test_guardrails.py), and [live walkthrough results](use-cases.md#live-walkthrough-results) show what was checked.

## 2. Prompt injection defenses

- Receipt lines and recipe inputs go to the models as structured data. The recipe prompt separates the selected constraints from the free-text meal request. Python applies the selected constraints to the returned recipes.
- Before an extracted receipt item enters the review table, ChefNova checks that its cited text appears in the filtered receipt and supports the item name. The user reviews the draft and chooses **Add reviewed items** to save it.
- The evidence check covers item names. Users still review amounts and units. Structured inputs and these checks reduce the impact of instruction-like text, with coverage limited to the cases tested.

Targeted tests include a receipt that tries to add a fake grocery item and a recipe request that conflicts with selected dietary restrictions. See the [guardrail tests](../tests/test_guardrails.py).

## 3. Recipe output validation

- Python validates the provider response and filters recipe candidates using the selected diet, maximum time, and ingredients to avoid. The dietary and avoid rules look for known terms in ingredient lists, instructions, and proposed substitutions.
- **Cook now** means the listed quantities fit positive pantry stock in matching units. **Check quantities** flags names that match when some amounts or units need verification. Missing items or a known shortfall reduce the pantry match.
- Known gaps include unit conversion, dietary word variants, and ingredients mentioned only in the steps. For example, a recipe that listed rice but added absent sesame oil in a cooking step still earned **Cook now**. Allergy safety, actual cooking time, and nutrition remain unverified.

See the [recipe validation code](../app/recipe_recommendations.py) and [offline cases](use-cases.md#offline-checks).

## 4. Recipe rate limits and fallback

- Recipe generation uses a 25-second request budget across configured providers. Groq goes first and can fall back to Gemini on a provider error, timeout, or invalid response when time remains. A valid empty response ends the request.
- On HTTP 429, the recipe flow puts the affected provider on cooldown in the current Streamlit session. It uses a positive numeric `Retry-After` value when available and otherwise sets a 15-second cooldown. Groq recipe requests use zero SDK retries.
- The UI guards against overlapping refreshes in the same session. If neither provider succeeds, the app preserves the confirmed pantry and displays a retry message.

The live recipe run deliberately elicited a real Groq HTTP 401. ChefNova switched to Gemini and returned a recipe in 1.42 seconds total. The recipe HTTP 429 cooldown and shared budget were verified with simulated failures. See the [live walkthrough results](use-cases.md#live-walkthrough-results) and [guardrail tests](../tests/test_guardrails.py).

## Data and credentials

| Data | Handling |
| --- | --- |
| Receipt image | Processed locally through a temporary file. Filtered OCR text is sent to the extraction provider. |
| Typed and voice input | Typed grocery text and voice transcripts are sent for grocery structuring. Voice audio is sent to Groq for transcription. Receipt-specific PII filtering applies to the receipt path. |
| Pantry and preferences | Saved per profile in local SQLite. Recipe requests send confirmed pantry items and selected constraints to the attempted provider. Local profile names identify records. The prototype has no authentication or formal retention policy. |
| API keys | Configure keys in the ignored `app/.env` file or use the session fields in the app. Keep `app/.env.example` as a blank template for credentials. |

## Reproduce the automated checks

From the repository root:

```bash
python -m pytest tests/test_guardrails.py tests/test_recipe_recommendations.py tests/test_recommendation_accuracy.py tests/test_ui_persistence.py -q
```

The suite covers receipt filtering and evidence checks, recipe constraints and quantities, provider fallback and cooldown, and pantry persistence. The [use-case guide](use-cases.md) separates those automated checks from real provider observations.
