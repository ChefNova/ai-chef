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

Provider failures in these tests are simulated. For live demo evidence, record the profile, input, selected constraints, provider shown in the recipe details, and observed result.
