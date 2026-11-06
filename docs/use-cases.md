# ChefNova use-case walkthroughs

These walkthroughs cover the Streamlit app on `stagging`. Use a disposable profile and synthetic data for the demo. A new profile may start with sample pantry items.

## Demo setup

1. Follow the [local setup guide](../app/INSTALL.md), then run `streamlit run ChefNova_app_UI.py` from the repository root.
2. Open **My Inventory** and enter your provider keys under **AI API Keys**. Either provider can run receipt extraction or recipe generation. Use both keys to exercise Groq-to-Gemini fallback. Voice transcription requires a Groq key and microphone permission.
3. Use a clear synthetic receipt for the primary flow. Keep a short typed grocery list ready for the recovery walkthrough.

## UC-1 · Build a pantry from a receipt, typed list, or voice

| Input | Steps | What to check |
| --- | --- | --- |
| **Receipt** | In **My Inventory**, open **Receipt**. Upload a PNG, JPG, JPEG, or WebP and click **Extract grocery items**. | Tesseract reads the image locally. ChefNova filters the OCR text before sending it to a provider, then checks the extracted items against the cleaned receipt. A receipt with no usable grocery lines can be entered manually. |
| **Type** | Open **Type**, enter “I have two cups of rice and one can of chickpeas,” then click **Convert to grocery table**. | The grocery list becomes an editable draft. Check the item names, amounts, and units. |
| **Voice** | Open **Voice** and use **Record grocery list** to say the same items. | Check the transcription and the resulting draft. If recording or transcription fails, use **Type**. |

In the review table, correct a quantity and click **Add reviewed items**. Open the pantry table and verify the saved value. Review applies to all three input methods. Saving the same receipt twice adds its quantities twice because there is no receipt deduplication.

## UC-2 · Confirm the pantry and rank recipes

1. In **My Inventory**, review the current pantry. If you edit it, click **Save pantry edits**, then click **Confirm Inventory**.
2. Open **Get Recipe**. Set **Diet**, **Maximum cooking time**, or **Avoid ingredients**. For example, request a vegan meal in 20 minutes using rice and chickpeas.
3. Click **Rank My Recipes**. Groq generates candidates first when configured. Gemini can take over if Groq fails or returns invalid output. Python validates, filters, and ranks the results locally. A valid empty response ends the provider request.
4. Review the results. The initial view shows up to three recipes. Click **View recipe** to see the listed ingredients, quantities when supplied, and cooking steps.

**What to check.** **Cook now** means the listed amounts fit the confirmed pantry in matching units. **Check quantities** flags amounts that need review. Missing ingredients affect the pantry match. Compare the recipe steps with the ingredient list and check any dietary restrictions directly.

**Live recovery.** Edit and save a pantry quantity, then try **Rank My Recipes** before reconfirming. The app should require confirmation again. Return to **My Inventory**, confirm the updated pantry, and rerun. This recovery works without inducing an external provider failure.

## UC-3 · Verify saved preferences and pantry state

1. Under **Get Recipe**, set **Diet**, **Maximum cooking time**, and **Avoid ingredients**.
2. Open a fresh session using the same profile. Return to **Get Recipe** and check that the settings are still selected.
3. Verify the saved groceries in **My Inventory**. The pantry and preferences persist in SQLite. The confirmation is specific to the session and must be repeated before ranking.

## UC-4 · Reset a disposable pantry

1. In the pantry table under **My Inventory**, click **Clear pantry**.
2. Reopen the same profile and verify that the pantry is still empty and saved preferences are still present.
3. Verify that recipe generation is blocked until groceries are added and the pantry is confirmed.

## Reproducible checks

Run from the repository root:

```bash
python -m pytest tests/test_guardrails.py tests/test_recipe_recommendations.py tests/test_ui_persistence.py -q
```

| Scenario | Expected result | Evidence |
| --- | --- | --- |
| Synthetic receipt includes personal details and an instruction to add a fake item | Both mocked providers receive cleaned text. The fake item fails the receipt evidence check. | [Guardrail tests](../tests/test_guardrails.py) |
| Receipt contains only sensitive metadata | Extraction returns manual review without calling either provider. | [Guardrail tests](../tests/test_guardrails.py) |
| Groq returns malformed JSON or a valid empty list | Malformed JSON can trigger Gemini fallback. A valid empty list does not. | [Recommendation tests](../tests/test_recipe_recommendations.py) |
| Groq returns a simulated `429` or uses most of the time budget | The provider goes on cooldown after a `429`. Gemini can use the remaining budget. Failed attempts leave the confirmed pantry intact. | [Guardrail tests](../tests/test_guardrails.py) |
| Amounts match, are insufficient, or use different units | The verified recipe can show **Cook now**. A shortfall affects the match and incompatible units can show **Check quantities**. | [Guardrail tests](../tests/test_guardrails.py) · [Streamlit tests](../tests/test_ui_persistence.py) |
| Pantry or preferences change, then the user starts a fresh session | Saved values persist for the same profile. The pantry needs confirmation again. | [Streamlit tests](../tests/test_ui_persistence.py) |

## Observed results

The team ran **36 real API requests on ChefNova** using six pantries and three attempts per provider per scenario. The benchmark called each provider independently and counted the recipes that passed local filtering. It ran before the guardrail update and did not exercise Streamlit or the automatic fallback chain. See the [raw results](../validation/recommendations/live-results.json) and [evaluation report](../validation/recommendations/REPORT.md).

| Provider | Attempts with at least one displayable recipe | Observed API errors |
| --- | ---: | --- |
| Groq | 3/18 | 14 rate-limit errors |
| Gemini | 12/18 | 3 server errors and 3 client errors |

| Synthetic input and constraints | Observed result |
| --- | --- |
| Rice, chickpeas, spinach, and garlic. Vegan, at most 20 minutes. | Groq and Gemini each produced displayable recipes on 2/3 attempts. Gemini returned **Garlic Chickpea Rice** on one attempt. |
| Rice, tofu, and broccoli. Vegan, at most 30 minutes, avoid peanut and groundnut. | Groq hit its rate limit on all three attempts. Gemini produced displayable recipes on all three, including **Simple Tofu and Broccoli Rice Bowl**. |
| Rice and spinach. Vegan, with a request for chicken and butter. | No displayable recipe on any attempt. Groq returned three rate-limit errors and Gemini returned three client errors. |

### offline checks

**Result: 19/19 passed.** Each case passes a hand-written model response through the same JSON parser and local recipe ranker used by the app. The runner compares the observed recipe titles and, where specified, parse status, match score, and readiness label against the case's expected values. The default pantry has one cup of rice. Some cases substitute a different pantry or apply explicit constraints. The tests do not call an AI provider or run OCR, voice transcription, or the browser UI.

Run just this corpus with `python -m pytest tests/test_recommendation_accuracy.py -q`. The inputs and assertions are in [cases.py](../validation/recommendations/cases.py) and [evaluate.py](../validation/recommendations/evaluate.py).

| # | Check | Expected and observed result |
| ---: | --- | --- |
| 1 | Vegan filter with chicken, milk, and rice candidates labeled vegan | Keeps rice and drops chicken and milk. |
| 2 | Vegetarian filter with yogurt and fish candidates | Keeps yogurt and drops fish. |
| 3 | 20-minute cap with recipes taking 21 minutes, an unknown time, and exactly 20 minutes | Keeps only the recipe at the 20-minute boundary. |
| 4 | Uppercase `PEANUT` in the avoid list | Drops the peanut butter recipe and keeps rice. |
| 5 | Pantry overlap versus provider order | Reorders the candidates by match to 100%, 50%, and 25%, with **Check quantities**, **Almost ready**, and **Needs shopping**, respectively. |
| 6 | Rice names with different capitalization and surrounding spaces | Recognizes the same ingredient and reports 100% overlap. |
| 7 | Fastest ranking priority | Puts the five-minute recipe above the 20-minute recipe despite its lower pantry match. |
| 8 | Highest protein ranking priority | Puts the recipe listing 30 g above the recipe listing 5 g despite its lower pantry match. |
| 9 | Fewest missing ingredients priority | Puts the rice-only recipe above the recipe that also needs lemon. |
| 10 | High-protein preference with equal pantry matches | Breaks the tie in favor of the recipe listing more protein. |
| 11 | Eggplant under the vegan filter | Keeps eggplant. The word boundary prevents it from matching egg. |
| 12 | Recipe with an empty ingredient list | Reports 0% overlap and **Needs shopping**. |
| 13 | Ingredient list contains both `Rice` and `rice` | Rejects the duplicate during parsing and returns no candidates. |
| 14 | Well-formed response with an empty recipes array | Accepts the response and returns no candidates. |
| 15 | Pantry contains rice with zero stock | Reports 0% overlap and **Almost ready** for the rice recipe. |
| 16 | Pantry contains `Chickpeas` and the recipe requests `Chickpea` | Recognizes the alias and reports 100% overlap. |
| 17 | Duck candidate under the vegetarian filter | Drops the duck candidate. |
| 18 | Feta candidate under the vegan filter | Drops the feta candidate. |
| 19 | Groundnut oil with `peanut` in the avoid list | Recognizes the alias and drops the recipe. |

These results apply to the cases above. For example, a 100% ingredient match can still show **Check quantities** when the recipe omits amounts.

### Live walkthrough results 
ChefNova's application functions were ran with real provider calls and synthetic inputs. It saved reviewed grocery rows to a disposable SQLite database and read them back. The harness exercised the same extraction, transcription, recipe, and storage code used by Streamlit. Browser widgets and microphone capture were outside this run.

| Walkthrough | Input and execution | Observed result |
| --- | --- | --- |
| Recipe generation and automatic fallback | Pantry with two cups of rice, one can of chickpeas, and one bag of spinach. Vegan, at most 20 minutes. First ran with both configured keys, then supplied a deliberately invalid Groq key to elicit a real HTTP 401. | Groq returned **Quick Vegan Rice & Chickpea Spinach Bowl** in 2.73 s, labeled **Needs shopping**. On the controlled failure, Groq returned HTTP 401 and ChefNova automatically used Gemini, which returned **Quick Chickpea Spinach Rice Bowl** in 1.42 s total, labeled **Almost ready**. This run verified recovery from authentication failure. The HTTP 429 cooldown still has simulated test coverage. |
| Receipt OCR, extraction, and save | Synthetic receipt with rice, chickpeas, bananas, and a loyalty ID. Used local Tesseract, then Groq. | Filtering kept all three grocery lines and removed the loyalty ID. Tesseract misread the banana price as 8.78 instead of 0.78. Groq still extracted **1.12 lb bananas** and left the rice and chickpea amounts unknown. During review, each single purchase line was saved as **1 count**. SQLite readback returned all three items. |
| Typed grocery entry | Typed “I have two cups of rice and one can of chickpeas.” | Groq returned **2 cups rice** and **1 can chickpeas**. Both amounts and units matched the SQLite readback. The flow took 1.20 s. |
| Voice grocery entry | Passed a synthesized recording of the same sentence to the app's voice transcription function. | Groq Whisper transcribed the sentence correctly. Grocery extraction returned **2 cups rice** and **1 can chickpeas**, both verified in SQLite. Transcription, extraction, and save took 1.13 s. |

