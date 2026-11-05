# ChefNova — Safety & Privacy

## Overview

ChefNova processes grocery receipt images and passes user pantry data to external LLM APIs. This document describes potential risks, implemented safeguards, and how those safeguards are tested.

---

## Potential risks

| Risk | Description |
|------|-------------|
| PII leakage | Receipt images may contain names, addresses, loyalty card numbers, or payment info |
| Prompt injection | Malicious text in a receipt could attempt to hijack the LLM prompt |
| Hallucinated recipes | LLM may suggest recipes with ingredients not in the pantry |
| API key exposure | Keys committed to version control or logged in plaintext |
| Excessive API spend | Unconstrained calls could incur large costs |

---

## Implemented guardrails

### 1 — PII sanitization (receipt extraction)

**What:** Before the extracted receipt text is passed to any LLM, `receipt_extractor.py` strips fields that are not food-item data.

**How:** The extraction prompt (`app/prompts/receipt_extraction.md`) instructs the model to ignore and not return: subtotals, taxes, totals, payment info, addresses, transaction numbers, register/cashier info, loyalty data, coupons, and barcodes. The validator (`receipt_validator.py`) discards any returned field not in the `GroceryItem` schema.

**Testing:** `tests/test_schemas.py` asserts that unexpected fields are rejected by the Pydantic model.

---

### 2 — Prompt injection mitigation

**What:** User-supplied content (OCR text, pantry item names) is inserted into prompts only via interpolated template slots, never appended as raw system instructions.

**How:** The recipe recommendations prompt wraps user data in a clearly delimited `Pantry:` block. The system message precedes it and cannot be overridden by content in that block.

**Limitation:** No formal adversarial testing has been conducted. This is a known gap for a future checkpoint.

---

### 3 — Output validation (hallucination guard)

**What:** Recipes returned by the LLM are cross-checked against the pantry inventory. Any recipe that includes an ingredient not in the pantry is flagged with a warning in the UI rather than silently presented.

**How:** `rank_recipes()` in `recipe_recommendations.py` compares each recipe's `ingredients` list against the session pantry. Missing ingredients are surfaced in the `missing_fields` output field.

**Testing:** `tests/test_recipe_recommendations.py` includes fixtures with recipes that reference out-of-pantry ingredients and asserts they are correctly flagged.

---

### 4 — API key handling

**What:** No API keys are committed to the repository.

**How:**
- `.env.example` provides the template with empty values and clear comments.
- `.env` is listed in `.gitignore`.
- CI runs `git grep -r 'GROQ_API_KEY=g' .` to fail if a real key pattern is ever staged.

**Verification:** Run `git log --all --full-history -- .env` — it should return no results.

---

### 5 — Rate limiting / cost controls

**What:** Each user session is limited to a maximum number of LLM calls per page load.

**How:** `recipe_recommendations.py` caps recommendation calls at **3 per session** using a Streamlit session state counter. If the cap is reached, the UI shows a "Refresh limit reached" message and disables the button.

**Estimated per-session cost:** ~$0.001–$0.005 USD depending on pantry size.

---

## Failure fallbacks

| Failure | Fallback behaviour |
|---------|-------------------|
| Groq API timeout / error | Retry once, then fall back to Gemini |
| Gemini API error | Show "Recommendations unavailable" message; no crash |
| LLM returns malformed JSON | Parser returns empty list; UI shows "Could not parse recipes" |
| Tesseract not installed | App shows clear install instructions and disables upload |
| Pydantic validation failure | Item is dropped from pantry; UI shows warning with item name |

---

## Known limitations and future work

- **No authentication:** Any local user can access the app. For a multi-user deployment, authentication would be required.
- **No data retention policy:** Session state is cleared on page refresh, but no formal data deletion guarantee exists.
- **Prompt injection:** No red-team testing has been done. Adversarial receipt content is a known gap.
- **Image privacy:** Receipt images are processed in-memory and never persisted to disk, but this is not independently audited.

---

## Testing safety properties

```bash
# Run the full test suite including schema / validation tests
pytest tests/ -v

# Check for accidentally committed secrets
git grep -rE '(GROQ_API_KEY|GEMINI_API_KEY)=[a-zA-Z0-9_-]{10,}' .
```
