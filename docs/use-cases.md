# ChefNova — Use-Case Walkthroughs

## UC-1: Upload a receipt and populate pantry

**Actor:** Home cook  
**Goal:** Parse a grocery receipt photo to build a pantry inventory

### Steps

1. User opens ChefNova at `http://localhost:8501`.
2. User clicks **Upload Receipt** and selects a photo (PNG or JPG).
3. `receipt_extractor.py` runs Tesseract OCR on the image, producing raw text.
4. The raw text is passed to the receipt extraction prompt; the LLM returns structured JSON.
5. `receipt_validator.py` validates each item with Pydantic; items below confidence threshold are flagged.
6. Validated items are added to the pantry panel in the UI.
7. User reviews the list, edits quantities if needed, and confirms.

**Expected outcome:** Pantry populated with grocery items; each item shows name, quantity, and unit.

**Edge cases tested:**

- Blurry or low-contrast receipt → OCR returns partial text; app shows a warning and lists extracted items only.
- Non-food items on receipt (e.g., detergent) → extractor filters them out per Rule 1 in the prompt.
- Duplicate receipt upload → user is prompted to merge or replace.

---

## UC-2: Get recipe recommendations from pantry

**Actor:** Home cook  
**Goal:** Receive actionable recipes using items currently in the pantry

### Steps

1. User sets optional dietary constraints (Vegan, Gluten-Free, etc.) and max cook time.
2. User clicks **Find Recipes**.
3. `recipe_recommendations.py` builds the prompt from pantry state and constraints.
4. App calls Groq API (primary); on failure, falls back to Gemini API.
5. A second call to Gemini Flash-Lite ranks the returned recipes by protein content, cook time, and pantry coverage.
6. Up to 5 recipe cards are displayed with ingredients, instructions, and substitution suggestions.

**Expected outcome:** Ranked recipe cards; each card shows title, estimated time, protein content, and step-by-step instructions.

**Edge cases tested:**

- Empty pantry → app shows "Add items to your pantry first" message; no LLM call made.
- LLM returns malformed JSON → parser falls back to raw text display with a warning.
- No recipes match constraints → LLM returns `[]`; app shows "No matching recipes found."
- Groq API timeout → automatic retry once, then Gemini fallback.

---

## UC-3: Adjust dietary profile

**Actor:** Home cook  
**Goal:** Persist dietary preferences across sessions

### Steps

1. User opens the **Profile** sidebar.
2. User selects one or more dietary tags (Vegan, Vegetarian, Gluten-Free, Halal, etc.).
3. Preferences are stored in Streamlit session state.
4. All subsequent recipe recommendation calls include the saved constraints automatically.

**Expected outcome:** Recipe results filtered to match dietary profile without manual re-entry each session.

---

## UC-4: Clear pantry

**Actor:** Home cook  
**Goal:** Reset pantry to start fresh

### Steps

1. User clicks **Clear Pantry** button.
2. Session state pantry list is reset to `[]`.
3. UI reflects empty pantry; previous receipt items are removed.

**Expected outcome:** Pantry is empty; subsequent recipe recommendations are blocked until items are re-added.

---

## Test case matrix

| Use Case | Happy Path | Empty Input | API Failure | Bad LLM Output |
|----------|------------|-------------|-------------|----------------|
| UC-1 Receipt upload | ✅ | ✅ | N/A | ✅ |
| UC-2 Recipe recommendations | ✅ | ✅ | ✅ (Groq→Gemini) | ✅ |
| UC-3 Dietary profile | ✅ | ✅ | N/A | N/A |
| UC-4 Clear pantry | ✅ | N/A | N/A | N/A |
