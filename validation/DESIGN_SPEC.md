# ChefNova — Design Specification
## CP2 Step 8: User Journeys, Flows, and Interaction Spec

**Project:** ChefNova (IS 492 CP2)  
**Author:** Chaitanya Nirantar  
**Date:** October 2026  
**Prototype:** Streamlit demo (`app.py`)  
**Branch:** `cp2/design-prototype`

---

## 1. Design Principles

These principles are load-bearing — every interaction decision in the prototype traces back to at least one of them.

### 1.1 Inventory Decision Rights

The user, not the system, decides what is in their kitchen. ChefNova interprets and recommends; it never silently updates the pantry from a receipt, a voice transcript, or a conversational message. Every proposed inventory change goes through a visible review step before it becomes pantry truth.

**Interaction consequence:** The "Add reviewed items" action is always a deliberate two-step: (1) parse/extract, (2) confirm. No single action skips directly to commit.

### 1.2 Hard Filters Before Ranking

Dietary requirements and maximum cooking time are constraints, not preferences. The system enforces them as exclusion criteria before scoring, so no recipe violating a hard filter can appear in recommendations regardless of how highly it would otherwise score.

**Interaction consequence:** Dietary and time fields are labeled "Hard filters" in the UI. Cuisine and protein preference are labeled "Ranking preferences." The distinction is visible in the form.

### 1.3 Temporary Conversational State Is Not Pantry State

Refinements made in the "Ask ChefNova" chat during a recommendation session (e.g., "I don't have spinach," "under 15 minutes") operate on a temporary overlay. They do not modify `st.session_state.inventory` or `st.session_state.confirmed`. A reset button restores the original recommendation state.

**Interaction consequence:** The system explicitly warns users that temporary statements "do not silently change your confirmed pantry." Temporary exclusions appear as pills in the active filter row.

### 1.4 Explainability Over Black-Box Ranking

Every recommendation shows its score, a plain-English "Why this?" reason, and a status label (Cook now / Almost ready / Needs shopping). The score formula is disclosed in an expandable section.

### 1.5 Separation of Input Mode From Review

Receipt upload, typed entry, and voice entry all funnel into the same review table before any item reaches the pantry. The input mode is an implementation detail of the acquisition step; the review/confirm step is identical regardless of how items arrived.

---

## 2. Application State Model

The following session-state variables constitute the shared application state. All pages read from and write to this state.

| Variable | Type | Default | Semantics |
|---|---|---|---|
| `page` | str | `"Home"` | Current view router target |
| `inventory` | list[dict] | `DEFAULT_INVENTORY` | Confirmed pantry items: `{Ingredient, Quantity, Unit}` |
| `confirmed` | bool | `False` | Whether the current inventory has been explicitly confirmed by the user |
| `request` | str | `""` | Free-text meal request; persists across Home and Get Recipe |
| `review_items` | list[dict] | `[]` | Proposed items awaiting user review before pantry commit |
| `messages` | list[dict] | `[]` | Conversational refinement history for current recommendation session |
| `selected_recipe_id` | str\|None | `None` | ID of the recipe currently open in Recipe Details |
| `temporary_exclusions` | list[str] | `[]` | Ingredient names excluded for the current session only |
| `conversation_max_time` | int\|None | `None` | Time ceiling set conversationally (overrides preference for this session) |
| `conversation_keywords` | list[str] | `[]` | Keywords extracted from conversational refinements |
| `diet_pref` | str | `"Vegetarian"` | Hard dietary filter |
| `max_time_pref` | str | `"20 min"` | Hard time ceiling (from preference form) |
| `cuisine_pref` | str | `"Any"` | Ranking preference for cuisine type |
| `priority_pref` | str | `"Best pantry match"` | Tiebreaker criterion in ranking |
| `high_protein_pref` | bool | `True` | Ranking bonus for high-protein recipes |
| `feedback` | dict | `{}` | Post-cook feedback per recipe ID |

**Confirmed flag semantics:** `confirmed` is set to `True` only by an explicit "✓ Confirm Inventory" action. It is set to `False` whenever `inventory` changes (save edits, add reviewed items). Unconfirmed inventory triggers a warning on the Get Recipe and Recommendations pages but does not block navigation.

---

## 3. Page Map and Navigation

```
Home
  ├─→ My Inventory       (via "Manage Inventory" or sidebar)
  ├─→ Get Recipe         (via "Find Recipes →" or sidebar)
  └─→ Recommendations    (via "Find Recipes →" when confirmed)

My Inventory
  ├─→ (stays on page)    (add, review, confirm)
  └─→ (no auto-navigation; user navigates manually)

Get Recipe
  └─→ Recommendations    (via "Rank My Recipes →")

Recommendations
  ├─→ Recipe Details     (via "View recipe" on any card)
  └─→ (stays on page)    (conversational refinement, reset)

Recipe Details
  └─→ Recommendations    (via "← Back to recommendations")

Evaluation Plan
  └─→ (standalone; no outbound navigation)
```

Sidebar navigation is always available and performs a direct page set + `st.rerun()`. It does not clear session state.

---

## 4. User Journeys

### Journey A — First-Time Setup (New User)

**Goal:** User arrives with no confirmed inventory and wants to get a recipe recommendation.

1. **Home:** User sees the hero section and "Find Recipes →" button. If they click it without confirming inventory, the system redirects to My Inventory with an informational message.
2. **My Inventory → Add groceries tab:** User chooses an input method (receipt / type / voice).
3. **Review table:** Proposed items populate the review data editor. User edits if needed.
4. **"Add reviewed items":** Items merge into the pantry. The `confirmed` flag is cleared.
5. **Current pantry tab:** User reviews the final pantry list and optionally edits further.
6. **"✓ Confirm Inventory":** `confirmed = True`. A toast confirms the action.
7. **Get Recipe:** User sets hard filters and ranking preferences, enters a free-text meal request.
8. **"Rank My Recipes →":** Temporary state is cleared, session is reset, page navigates to Recommendations.
9. **Recommendations:** Three ranked recipe cards appear with scores, status labels, and "Why this?" explanations.
10. **"View recipe":** Recipe Details shows ingredient availability, steps, and substitutions.

**Decision point at step 1:** If the user ignores the redirect and navigates directly to Get Recipe, a warning banner appears but they can still proceed. Recommendations will show with a warning that inventory is not confirmed.

---

### Journey B — Pantry-First Weeknight Cook

**Goal:** "I have stuff in my fridge. What can I make in 20 minutes?"

1. **Home:** User types "quick dinner" in the request field.
2. Navigates to Get Recipe, keeps "20 min" hard filter, selects "Best pantry match" priority.
3. **Recommendations:** Recipes labeled "Cook now" appear first. User picks one.
4. **Recipe Details:** Sees "✓ Available" for all required ingredients. Follows the step-by-step instructions.
5. Rates the recipe with 👍/😐/👎 after cooking.

**Key interaction:** The "Cook now" status label is only displayed when zero required ingredients are missing from the confirmed pantry. The system does not label a recipe "Cook now" if `confirmed = False`.

---

### Journey C — Conversational Refinement

**Goal:** User wants to narrow results without going back to the preference form.

1. User is on the Recommendations page and sees spinach-heavy recipes.
2. User types in the chat: "I don't have spinach."
3. `process_refinement()` detects a negative pattern + a known ingredient. "Spinach" is added to `temporary_exclusions`.
4. The system responds: "I excluded recipes requiring Spinach for this search. Your confirmed pantry was not changed."
5. `st.rerun()` re-runs `ranked_recipes()` with spinach excluded. The recommendations update.
6. A "Spinach excluded" pill appears in the active filter row.
7. User clicks "Reset conversational refinements" to restore the original results.

**Interaction rules:**
- Temporary exclusions are session-scoped to the current recommendation view.
- They appear as filter pills in the UI header so the user can see what is active.
- "Reset conversational refinements" clears `temporary_exclusions`, `conversation_max_time`, and `conversation_keywords`, and empties the chat history.
- Typing "under 15 minutes" sets `conversation_max_time = 15`, overriding `max_time_pref` for this session only.

---

### Journey D — Voice-First Entry

**Goal:** User wants to add groceries by speaking, not typing.

1. **My Inventory → Add groceries → Voice tab:** User records a grocery list.
2. `st.audio_input` captures audio. A hash check prevents double-processing on Streamlit reruns.
3. `speech_to_text()` sends the audio to Google's speech API. If `SpeechRecognition` is not installed, the tab degrades gracefully with a warning message.
4. The transcript is passed to `parse_grocery_text()`, which returns structured `{Ingredient, Quantity, Unit}` dicts.
5. `review_items` is populated. The user sees the review table with the parsed result.
6. User edits any misrecognized items and clicks "Add reviewed items."

**Failure handling:**
- If the API call fails, the error is surfaced with a `st.warning()` message. The review table remains empty. The user is not shown a cryptic exception.
- If the transcript is non-empty but `parse_grocery_text` returns no items, a warning suggests separating items with commas.

**Audio hash guard:** `last_inventory_audio_hash` (and `last_refine_audio_hash` on the recommendations page) prevent re-processing a recording that was already handled. Without this guard, Streamlit's rerun cycle would re-process audio on every widget interaction.

---

### Journey E — Receipt Upload

**Goal:** User uploads a grocery receipt image to seed their pantry.

1. **My Inventory → Add groceries → Receipt tab:** User uploads a PNG, JPG, or PDF.
2. `st.file_uploader` accepts the file. A success message confirms the filename.
3. User clicks "Extract grocery items."
4. `prototype_receipt_extraction()` is called. In the prototype, this returns a fixed demo dataset regardless of the actual file content. **This function is the designated integration point for the OCR/Vision backend.**
5. The extracted items populate `review_items`. An info message tells the user this is prototype extraction.
6. User edits the review table and adds items.

**Architecture note:** The prototype boundary is clearly documented in the function docstring: "Replace this function with actual receipt OCR/API extraction later." The review/confirm flow is fully functional and production-ready; only the extraction step is stubbed.

---

## 5. Component Interaction Spec

### 5.1 Inventory Review Editor

**Location:** My Inventory → Add groceries tab (right column)

| Behavior | Specification |
|---|---|
| Input | `st.session_state.review_items` (list of dicts) |
| Widget | `st.data_editor` with `num_rows="dynamic"` |
| Columns | Ingredient (text, required), Quantity (number, min 0), Unit (text) |
| "Add reviewed items" | Disabled when `edited_review_df.empty`. On click: calls `merge_inventory_items()`, clears `review_items`, sets `confirmed = False`, reruns. |
| "Clear review" | Disabled when empty. On click: clears `review_items`, reruns. |
| Merge behavior | If an ingredient with the same name and unit already exists in inventory, its quantity is summed. Otherwise a new row is appended. |

### 5.2 Pantry Editor

**Location:** My Inventory → Current pantry tab

| Behavior | Specification |
|---|---|
| Input | `st.session_state.inventory` |
| Widget | `st.data_editor` with `num_rows="dynamic"` |
| "Save pantry edits" | Filters out rows with blank Ingredient. Normalizes names with `.strip().title()`. Sets `confirmed = False`. Reruns. |
| "✓ Confirm Inventory" | Disabled when inventory is empty. Sets `confirmed = True`. Fires `st.toast()` with confirmation message. Reruns. |
| Status display | `st.info()` shows current confirmed state and item count. |

### 5.3 Recipe Scoring Engine

**Function:** `score_recipe(recipe)`

The scoring engine applies hard filters first, then assigns a 0–100 point score:

| Component | Weight | Calculation |
|---|---|---|
| Pantry match | 40 pts | `(available_ingredients / required_ingredients) × 40` |
| Preference match | 25 pts | Cuisine match (8–12 pts) + protein preference (up to 8 pts) + keyword match from request (up to 5 pts) |
| Cooking time | 20 pts | `max(5, 20 − max(time − 10, 0) × 0.6)` — favors recipes ≤ 10 min, penalizes longer ones |
| Priority criterion | 15 pts | Determined by `priority_pref`: pantry ratio, speed, protein, or fewest missing |

**Hard filters that return `None` (recipe excluded entirely):**
- `recipe_is_diet_compatible()` returns False for the selected diet
- Recipe time exceeds `effective_max_time()`
- Any required ingredient appears in `temporary_exclusions`

**Status labels:**
- **Cook now:** zero required ingredients missing
- **Almost ready:** 1–2 required ingredients missing
- **Needs shopping:** 3+ required ingredients missing

### 5.4 Conversational Refinement Engine

**Function:** `process_refinement(text)`

The engine applies deterministic pattern matching in this priority order:

1. **Ingredient exclusion:** If a known ingredient name is detected AND a negative phrase appears ("don't have," "do not have," "no," "without," "don't want," "do not want") → add to `temporary_exclusions`.
2. **Time limit:** If a numeric minute pattern is detected → set `conversation_max_time`.
3. **Spicy keyword:** Add "spicy" to `conversation_keywords`.
4. **Quick/faster keyword:** Set `priority_pref = "Fastest"`.
5. **Protein keyword:** Set `high_protein_pref = True`, `priority_pref = "Highest protein"`.
6. **Fallback:** Generic reply: "I used that request to rerank the current recipe options."

Every refinement appends a `{"role": "user"}` and `{"role": "assistant"}` message to `st.session_state.messages`, which renders as a chat history below the recommendation cards.

**Scope:** `process_refinement` never writes to `st.session_state.inventory` or `st.session_state.confirmed`.

### 5.5 Recipe Card

**Location:** Recommendations page (up to 3 cards in a column grid)

Each card renders:
- Score badge (e.g., "87% ChefNova match")
- Status pill: Cook now (green) / Almost ready (amber) / Needs shopping (red-orange)
- Recipe title, time, protein, diet
- Tag pills
- "Why this?" reason string (plain English, up to 3 clauses)
- Missing ingredient count or "No required ingredients missing"
- "View recipe" button → navigates to Recipe Details

### 5.6 Recipe Details Page

Renders two columns:

**Left column:** Recipe card (emoji hero, ingredient list with ✓/! symbols, step-by-step instructions)

**Right column:**
- Score and reason summary
- Inventory check: "Available" list (green) and "Missing" list (orange)
- Substitution suggestions for missing ingredients (from `recipe["substitutions"]`)
- Post-cook feedback buttons (👍 Loved / 😐 Okay / 👎 No)
- "← Back to recommendations" button

**Inventory check logic:** Uses `inventory_names(include_temporary_exclusions=True)` — temporary exclusions are reflected in the availability display, so the Recipe Details page stays consistent with what the user stated in the chat.

---

## 6. Constraint Handling Model

This section maps the constraint types identified in **Gap 03 — Constraint Hierarchy Flattened** to the current prototype's implementation and the future design target.

| Constraint tier | Example | Current prototype | Target design |
|---|---|---|---|
| **Allergy (non-negotiable)** | Peanut allergy | Treated as diet hard filter (binary in/out) | Dedicated allergy profile; hard block with no override path; explicit warning when a recipe contains the allergen even if filtered |
| **Dietary restriction** | Vegetarian | `diet_pref` hard filter; excludes non-compliant recipes before scoring | Same; extend to per-household-member profiles |
| **Dislike (soft)** | No mushrooms | `temporary_exclusions` via conversational refinement | Persisted preference with override path ("include anyway for special occasions") |
| **Preference (ranking)** | Prefers spicy | `conversation_keywords` and `priority_pref` | Ranking signal only; transparent in score breakdown |

**Current prototype limitation:** All dietary constraints are modeled as a single `diet_pref` string. The four-tier model requires a structured constraint object with a `tier` field and different UI affordances for each tier. Allergy-tier constraints must never appear in recipe results without an explicit warning; they should not be overridable from a conversational message.

---

## 7. Input Parsing Specification

### 7.1 `parse_grocery_text(text)`

Deterministic rules (no AI):

1. Strip common preamble phrases: "I have," "I bought," "I got," "add," "we have," "we bought."
2. Split on commas and the word "and."
3. For each part: strip "some" / "about" prefix.
4. Tokenize by whitespace.
5. Parse leading token as quantity: numeric string → float, word in `number_words` → int, else default to 1.
6. Parse next token as unit if it appears in `unit_map`; consume "of" if it follows the unit.
7. Remaining tokens form the ingredient name, title-cased.
8. Apply heuristic unit defaults for uncounted food words (rice, milk, yogurt → "item").

**Limitations (documented for future improvement):**
- Does not handle "a dozen eggs" (dozen is in the map but requires awareness of the noun following it)
- Does not handle "half a cup of" (fractions)
- Does not resolve ambiguous ingredient names ("chips" → unresolved)

### 7.2 `prototype_receipt_extraction(filename)`

Returns a fixed demo dataset. Integration point for production OCR:

```python
# Future: send `filename` to receipt-parsing API or Vision model
# Return: list of {"Ingredient": str, "Quantity": number, "Unit": str}
```

The output format is identical to `parse_grocery_text()` so the downstream review/confirm flow requires no changes when this function is replaced.

---

## 8. Error and Edge Case Handling

| Scenario | Current behavior |
|---|---|
| `SpeechRecognition` not installed | `sr = None`; voice tab renders but calls degrade to a warning message |
| Speech API transcription fails | `st.warning()` with the exception message; review table left empty |
| No grocery items found in typed/voice input | `st.warning()` prompting the user to use commas |
| No recipes pass hard filters | `st.warning()` suggesting the user relax time or diet constraints |
| `selected_recipe_id` not in `RECIPE_DB` | `st.warning()` + "Back to recommendations" button |
| Empty inventory, "Confirm" clicked | Button is disabled (`disabled=len(st.session_state.inventory) == 0`) |
| "Add reviewed items" with empty review | Button is disabled (`disabled=edited_review_df.empty`) |
| Audio input rerun loop | Hash guard (`last_inventory_audio_hash`, `last_refine_audio_hash`) prevents double-processing |

---

## 9. Not-Yet-Implemented Design Decisions

These are gaps identified during prototyping and interviews that are documented here as future work, not currently in the prototype:

| Gap | Label | Design intent |
|---|---|---|
| Gap 01 | Inventory Decision Rights | Receipt extraction should propose; user confirms. ✅ Implemented. |
| Gap 02 | Silent Gap-Closing | AI should not hallucinate missing ingredients into a recipe it cannot make. Future: retrieval-backed recipe database. |
| Gap 03 | Constraint Hierarchy Flattened | Four-tier constraint model (allergy / diet / dislike / preference) with different UI and enforcement per tier. |
| Gap 04 | Feasibility ≠ Ingredient Match | "Cook now" should account for pantry quantities, not just ingredient presence. |
| Gap 05 | Trust Without Provenance | Substitution suggestions and nutrition data should carry confidence or source labels. |
| Gap 06 | Pantry-First ≠ Goal-Driven Planning | Dual entry points: "Cook Now" (pantry-first) and "Plan a Meal" (recipe-first, shopping-list output). |

---

## 10. Prototype Scope Summary

| Feature | Status |
|---|---|
| Receipt upload (review/confirm flow) | ✅ Functional; extraction is stubbed |
| Typed grocery entry | ✅ Functional |
| Voice grocery entry | ✅ Functional (requires `SpeechRecognition`) |
| Pantry editor (edit, save, confirm) | ✅ Functional |
| Hard filter enforcement | ✅ Functional |
| Explainable recipe ranking | ✅ Functional |
| Status labels (Cook now / Almost ready / Needs shopping) | ✅ Functional |
| Conversational refinement | ✅ Functional (deterministic) |
| Substitution suggestions | ✅ Functional (curated dataset) |
| Post-cook feedback | ✅ Functional (session-scoped) |
| Household profiles | ❌ Not implemented |
| Four-tier constraint model | ❌ Not implemented |
| Quantity-aware feasibility | ❌ Not implemented |
| Nutrition provenance labels | ❌ Not implemented |
| Plan a Meal (recipe-first) mode | ❌ Not implemented |
| Production receipt OCR | ❌ Stubbed |
| Production recipe database | ❌ Curated demo set only |
