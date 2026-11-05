# ChefNova use cases

Walkthroughs for the app served by `ChefNova_app_UI.py` on `cp3/chefnova-implementation`. Labels below are the ones on those screens.

Run the checks from the repo root:

```bash
PYTHONPATH=. python3 -m pytest tests -q
```

The recommendation tests use fixture model responses. They do not call Gemini or Groq. The persistence tests run the app against a temporary SQLite file. There is no automated test for the receipt screen or voice input. Streamlit's test runner cannot type into the pantry table, so those tests simulate what the table returns.

A new profile starts with six pantry rows. Those rows are starter data, not a receipt scan: Rice 2 cups, Chickpeas 2 cans, Spinach 1 bag, Tomatoes 4 count, Greek Yogurt 1 container, Garlic 1 bulb. They are saved once, when the profile is created. The pantry is listed alphabetically. Every session starts at status **Needs review**, including a return visit. Ranking does not read the demo recipe list in the source file. Gemini proposes recipes, then the app filters that response.

The sidebar has a **Profile** field, then **Home**, **My Inventory**, **Get Recipe**, and **Evaluation Plan**. Evaluation Plan lists suggested receipt sources and target metrics. It does not change the pantry and it does not call a model.

API keys typed on My Inventory stay in the browser session. The app does not write them into the repo or the database.

## 1. Open the app

**Steps**

1. Open the running ChefNova app.
2. Read the home heading and the sidebar inventory status.
3. Choose **Find Recipes**.

**Expected result**

- The home heading is “What can we cook with what you have?”
- The meal box placeholder is “e.g. I want a quick vegetarian dinner with lots of protein...”
- The sidebar says **! Needs review** and **6 pantry items**.
- **Find Recipes** opens **My Inventory**, because the pantry is not confirmed.
- **Manage Inventory** and **View Inventory** also open My Inventory.
- **Set Preferences** opens Get Recipe. That page warns: “Your inventory is not confirmed. Confirm it first so ChefNova can accurately label recipes as Cook now / Almost ready.”

**Matching test**

`test_first_visit_shows_the_documented_starter_state` in `tests/test_ui_persistence.py`

## 2. Enter a Gemini key

**Steps**

1. Open **My Inventory**.
2. Stay on **＋ Add groceries**.
3. In **Gemini API key**, type a key. The field is a password field. The placeholder is “Enter Gemini API key”.
4. Leave **Groq API key** empty if you want receipt extraction to use Gemini. If a Groq key is also filled, receipt and typed-list extraction try Groq first.

**Expected result**

- The caption under the key heading says keys are used only for this session and are not written to the repository, database, or logs.
- **Extract grocery items** stays disabled until a receipt file is chosen and at least one of the two key fields is non-empty.
- Recipe ranking uses this Gemini key. If the field is empty, ranking uses the `GEMINI_API_KEY` environment variable. Ranking does not use the Groq key.
- With a confirmed pantry and neither a session Gemini key nor `GEMINI_API_KEY`, **Rank My Recipes** opens Recommendations and shows: “Add a Gemini API key on the receipt tab, or set GEMINI_API_KEY. Nothing was sent.” No recipe cards appear. The model is not called.

**Matching test**

- `test_missing_key_does_not_call_the_model` in `tests/test_recipe_recommendations.py`
- `test_prompt_includes_pantry_and_hard_filters` checks that the key text is not copied into the prompt
- `test_gemini_complete_uses_the_receipt_client_and_flash_lite` checks the ranking call uses `gemini-3.5-flash-lite` and closes the client

## 3. Upload a receipt

**Steps**

1. On **My Inventory → ＋ Add groceries → Receipt**, enter a Gemini key, a Groq key, or both.
2. Upload a `.png`, `.jpg`, `.jpeg`, or `.webp` receipt.
3. Click **Extract grocery items**.

**Expected result**

- After the file is chosen, the page says “Receipt ready:” plus the file name.
- The uploader help text says ChefNova runs local Tesseract OCR, then Groq, with Gemini as the fallback model.
- The button shows “Reading receipt and extracting grocery items...”
- OCR runs on the image. If a Groq key is present, Groq (`qwen/qwen3.8-27b`) is tried first. If Groq is skipped or fails and a Gemini key is present, Gemini (`gemini-3.8-flash`, then `gemini-3.6-flash` on a deadline error) is the fallback.
- Groq success: “Receipt extracted with Groq. Review every item before adding it to your pantry.”
- Gemini fallback success: “Groq was unavailable, so ChefNova used Gemini fallback. Review the extracted items carefully.”
- Rows appear in **2. Review before adding**. They are not in Current pantry yet.
- A row is flagged when its review reason is non-empty. The page then warns “N extracted item(s) need review before being added to your pantry.” Flagged rows can still be edited and added. The **Needs Review** checkbox cannot be toggled.
- Review reasons the screen can show:
  - “Quantity could not be interpreted as a number.”
  - “Unusually large weight; verify the receipt.” for kilograms over 20, grams over 50000, pounds over 100, or ounces over 5000
  - “Package size looks implausibly large; verify the receipt.” when the package text contains 175 kg, 250 kg, or 500 kg
  - “Low extraction confidence; verify this item.” when confidence is under 0.80
  - “Confidence value could not be interpreted.”

**Matching test**

None for this screen. `test_grocery_item_validates_confidence` and `test_receipt_extraction_contains_items` in `tests/test_schemas.py` only check that a receipt item can store a name, quantity, unit, confidence, and source line.

## 4. Handle an unreadable receipt

**Steps**

1. Enter a Gemini or Groq key.
2. Upload an image the app accepts, then click **Extract grocery items**.
3. Use a picture with no readable text, or a picture whose text the models cannot turn into grocery items.

**Expected result**

- If OCR returns no text, the page shows “Receipt extraction failed: OCR returned no text from the receipt.” The review table is not filled. Nothing is added to the pantry.
- A missing OCR install fails the same way: “Receipt extraction failed:” plus the exception. The pantry is unchanged.
- If OCR returns text but Groq and Gemini both fail, or are both skipped, the page warns: “AI extraction was unavailable. Review the OCR text and enter the grocery items manually.” **View AI extraction errors** lists the provider errors. **View OCR text** shows the OCR string when there is one. The review table stays empty. No grocery rows are invented.
- Other image types are not offered by the uploader. A file that still reaches extraction with a different suffix fails with “Receipt extraction failed: Supported images: .jpg, .jpeg, .png, .webp”.

**Matching test**

None.

## 5. Review and correct extracted items

**Steps**

1. Extract a receipt, or convert a typed list, so the review table has rows.
2. Change an ingredient name, quantity, or unit. Add or delete a row if needed.
3. Leave a row with a blank ingredient, and correct one row you want to keep.
4. Click **Add reviewed items**.
5. Open **Current pantry** and check the list.

**Expected result**

- The review columns are Ingredient, Quantity, Unit, Package Size, Brand, Confidence, Needs Review, and Review Reason.
- Ingredient, Quantity, Unit, Package Size, and Brand can be edited. Confidence, Needs Review, and Review Reason cannot.
- **Add reviewed items** and **Clear review** are disabled while the table is empty.
- **Clear review** drops the table and does not change the pantry.
- **Add reviewed items** copies only ingredient, quantity, and unit. Package size, brand, and confidence are not stored in the pantry.
- A blank ingredient is skipped. A kept name is stored in title case. The same ingredient name and the same unit add their quantities together. A different unit is a separate row.
- After the refresh, the review table is empty, the new rows are on Current pantry, and the status is **Needs review** even if it was confirmed before. Confirm the pantry again before ranking.
- If any row cannot be saved, the page says “Nothing was saved.” and why. The pantry does not change and the review table keeps its rows.

**Matching test**

- `test_reviewed_items_are_there_in_the_next_session`
- `test_adding_to_a_saved_item_adds_the_quantities`
- `test_invalid_row_shows_an_error_and_saves_nothing`

## 6. Confirm the pantry

**Steps**

1. Open **My Inventory → Current pantry**.
2. Check the six starter rows, or the rows you added.
3. Click **✓ Confirm Inventory**.
4. Read the sidebar.

**Expected result**

- The button is enabled when the pantry has at least one row.
- A toast says “Inventory confirmed. ChefNova will now use it for recipe feasibility.”
- The status line says **Confirmed** and the item count.
- The sidebar says **✓ Confirmed**.
- **Save pantry edits** saves the editor contents to the database, title-cases names, and sets the status back to **Needs review**. Rows in the table with the same name and unit are added together. Confirm again after a save.
- Adding reviewed items also returns the status to **Needs review**.
- A change to the pantry from another tab or the API also returns the status to **Needs review** on the next interaction.

**Matching test**

- `test_confirmation_lasts_within_a_session_while_the_pantry_is_unchanged`
- `test_saving_edits_clears_the_confirmation`
- `test_change_from_another_tab_clears_the_confirmation_and_shows_up`

## 7. Enter ingredients manually

**Steps**

1. Open **My Inventory → ＋ Add groceries → Type**.
2. Enter a Gemini or Groq key.
3. Type a list, for example the placeholder: “I bought two pounds of chicken, one bag of spinach, 32 oz Greek yogurt, and six tomatoes.”
4. Click **✨ Convert to grocery table**.
5. Review the table, then click **Add reviewed items**.
6. On **Current pantry**, add a row in the editor, then click **Save pantry edits**.

**Expected result**

- **Convert to grocery table** is disabled until the box has text.
- With no Gemini key and no Groq key, the page errors: “Enter a Gemini or Groq API key first.” The pantry is unchanged.
- Groq success: “Groq converted N grocery item(s). Review the table on the right.”
- If Groq fails and Gemini returns items: “Groq failed, so Gemini fallback converted N item(s). Review carefully.”
- If the model call fails: “AI grocery extraction failed.” plus the provider error. No rows are invented from a local guess.
- Added review rows follow the same pantry rules as a receipt. Saving a hand-typed pantry row marks the inventory **Needs review**.
- The **Voice** tab is separate. It needs a Groq key and uses Whisper (`whisper-large-v3-turbo`). Without that key it warns “Enter a Groq API key to use voice input.” A successful transcript is structured with the same Groq-then-Gemini path as the Type tab, then it waits in the review table.

**Matching test**

None.

## 8. Rank recipes with diet, time, and avoid filters

**Steps**

1. Confirm the pantry.
2. Open **Get Recipe**.
3. Type a meal request.
4. Set **Diet**, **Maximum cooking time**, and **Avoid ingredients**. Avoid accepts commas, semicolons, or new lines. The placeholder is “peanuts, shellfish”.
5. Set **Cuisine**, **Prioritize**, and **Prefer high protein** if you want them. Cuisine is not a hard filter.
6. Click **Rank My Recipes**.
7. On Recommendations, open a card with **View recipe**.
8. Optional: in **Ask ChefNova**, type a refinement such as “make it under 15 minutes” or “I don't have spinach”.

**Expected result**

- Defaults for a new profile are Diet **Vegetarian**, Maximum cooking time **20 min**, Cuisine **Any**, Prioritize **Best pantry match**, and **Prefer high protein** checked. Changing one of these saves it for later sessions.
- If the pantry is not confirmed, the button stays on Get Recipe and warns: “Confirm your inventory first so ChefNova knows what you actually have.” Nothing is sent.
- A confirmed pantry with a Gemini key calls `gemini-3.5-flash-lite` once. The caption on Get Recipe says diet, time, and avoid are hard filters, and that an empty pantry or a missing key is not sent.
- Recommendations shows the active filters as pills. Each card shows a pantry-match percent, **Cook now**, **Almost ready**, or **Needs shopping**, time, protein, and diet. Missing time is “time not listed”. Missing protein is “protein not listed”. At most three cards are shown. The model is asked for at most four recipes.
- **Cook now** means every listed ingredient is in the pantry. **Almost ready** means one or two are missing. **Needs shopping** means three or more are missing, or the ingredient list was blank. The percent is that overlap.
- A vegan diet keeps only recipes labeled Vegan, and drops a recipe whose ingredients include meat or animal products such as egg, milk, cheese, yogurt, butter, honey, cream, ghee, paneer, or whey. A vegetarian diet keeps Vegetarian and Vegan labels and drops meat ingredients. **No preference** does not drop recipes for diet. A chicken recipe labeled Vegetarian is still dropped for a vegan or vegetarian diet.
- A time limit drops recipes with no listed time and recipes over the limit. An avoid term drops a recipe when the term is contained in an ingredient name, or the ingredient name is contained in the term.
- If every returned recipe fails those filters, the page warns: “No returned recipes satisfy the current hard filters. Try a longer time, a different diet, or a shorter avoid list.”
- If the model returns a valid empty recipe list, the page warns: “Gemini returned no recipes. No meals were invented to fill the gap.”
- A valid recipe with a null time or protein is still shown. The card notes “Cooking time was not returned.” or “Protein was not returned.” Those values are not filled in. If a time limit is set, a recipe with no time is hidden by that filter.
- **Ask ChefNova** re-filters the recipes already returned. It does not call Gemini and it does not change the confirmed pantry. “under 15 minutes” hides recipes over that time and recipes with no time. “I don't have spinach” hides recipes that use spinach for this list only. “faster” or “quick” reorders by listed time. “protein” reorders by listed protein. “spicy” is stored for the next Gemini request and does not change the cards on screen.
- **Ask Gemini again** sends a new request. It requires a confirmed pantry. **Reset conversational refinements** appears only after a chat refinement and clears those temporary limits.
- Recipe details list ingredients with a check or a bang, the steps, the pantry match, and substitutions for missing ingredients when the model named that ingredient. **Loved**, **Okay**, and **No** are stored for the session only. They do not change the pantry or the ranking.

**Matching test**

- `test_diet_violations_are_dropped_and_a_valid_recipe_remains`
- `test_pantry_matching_assigns_cook_almost_and_shopping_buckets`
- `test_prompt_includes_pantry_and_hard_filters`
- `test_partial_recipe_is_shown_with_missing_fields_marked`
- `test_gemini_complete_uses_the_receipt_client_and_flash_lite`

## 9. Empty pantry

**Steps**

1. Open **Current pantry**.
2. Delete every row.
3. Click **Save pantry edits**.
4. Try **✓ Confirm Inventory**.
5. Open **Get Recipe** and click **Rank My Recipes**.

**Expected result**

- The status is **Needs review** and **0 item(s)**. The sidebar says **0 pantry items**.
- **✓ Confirm Inventory** is disabled, so this screen cannot mark an empty pantry confirmed.
- **Rank My Recipes** stays on Get Recipe and warns: “Confirm your inventory first so ChefNova knows what you actually have.” No model request is made.
- The ranking function behind that button, if it is run with no named pantry items, does not call the model. Recommendations would show: “Add at least one confirmed pantry item before ranking. No recipes were invented.” The Confirm button does not create that state while the table has zero rows. Saving edits also clears a previous confirmation.
- The pantry is still empty in the next session. The starter rows do not come back.

**Matching test**

- `test_empty_pantry_does_not_call_the_model`
- `test_emptied_pantry_stays_empty_and_is_not_seeded_again`

## 10. Invalid or inconsistent model output

**Steps**

1. Confirm a pantry that has at least one ingredient, and enter a Gemini key.
2. Click **Rank My Recipes**.
3. This screen path is the live call. The failure cases below are what Recommendations shows when that call returns a bad payload, or when parsing the same payloads in the test fixtures.

**Expected result**

- The page shows the error and no recipe cards. It does not replace the bad payload with demo recipes.
- Text that is not JSON: “The model did not return valid JSON. No recipes were shown.”
- JSON that is not an object with a `recipes` list: “The model response did not contain a recipe list. No recipes were shown.”
- A recipe that is not an object, a blank ingredient, a repeated ingredient, a substitution for an ingredient that is not in that recipe, or instructions that are not text: “The model returned inconsistent ingredients. No recipes were shown.” One bad recipe fails the whole response.
- A model or network exception: “Recipe ranking failed” plus the exception type and a shortened message, then “No recipes were shown.” A key in the message is redacted.
- A valid recipe with unknown minutes, protein, diet, title, or steps is not this failure. It is shown, and those fields are marked missing. See use case 8.

**Matching test**

- `test_invalid_json_returns_no_recipes`
- `test_inconsistent_ingredients_return_no_recipes`
- `test_partial_recipe_is_shown_with_missing_fields_marked` covers the valid partial recipe, which is shown rather than dropped

## 11. Come back later

**Steps**

1. In the sidebar, type a name in **Profile** and press Enter.
2. Add groceries, then set **Diet**, **Maximum cooking time**, **Avoid ingredients**, and **Cuisine** on **Get Recipe**.
3. Open another page, then come back to **Get Recipe**.
4. Refresh the browser, or stop the app and start it again and open the same address.

**Expected result**

- The new profile starts from the same starter rows and defaults as a first visit. The address gains `?profile=` and the name in lowercase, so a refresh stays on that profile.
- The filters are unchanged after visiting another page. They do not reset to the defaults.
- After the refresh or restart, the pantry and preferences are the ones saved. Opening the address without `?profile=` shows the `default` profile.
- The status is **Needs review** after the refresh or restart, even if the pantry was confirmed before. Confirm it again before ranking.
- A chat refinement such as “make it faster” is not saved. Neither are the Gemini and Groq keys.
- Switching **Profile** returns to Home and clears the review table, recommendations, and chat from the previous profile. API keys stay for the browser session.
- A name with characters other than letters, numbers, spaces, `.`, `_`, or `-` shows an error, and the current profile stays open. The field is not a login, so anyone using the same deployment can open any profile.
- If the database cannot be opened, the page says “ChefNova could not open its saved pantry” and stops.

**Matching test**

- `test_preferences_are_there_in_the_next_session`
- `test_hard_filters_survive_leaving_the_page`
- `test_hard_filters_still_apply_after_ranking_and_more_clicks`
- `test_pantry_table_edits_are_there_in_the_next_session`
- `test_confirmation_does_not_carry_over_to_a_new_session`
- `test_chat_refinements_stay_temporary`
- `test_api_keys_are_never_written_to_the_database`
- `test_url_keeps_a_refresh_on_the_same_profile`
- `test_switching_profile_leaves_nothing_from_the_old_one`
- `test_invalid_profile_name_is_refused_and_keeps_the_current_one`
- `test_unusable_database_shows_an_error_instead_of_crashing`
- `test_data_survives_a_separate_process` in `tests/test_storage.py`

## 12. Use the storage API

**Steps**

1. Run `uvicorn app.api:app --reload` from the repo root.
2. Open <http://127.0.0.1:8000/docs>.
3. Create a profile with `PUT /api/v1/users/{username}`.
4. Add, read, edit, and delete pantry items, then change preferences.
5. Open the app with `?profile=` and the same name.

**Expected result**

- The app shows what the API saved, and the API returns what the app saved. They use the same database.
- Adding an item with a name and unit already in the pantry adds the quantities and returns 200. A new row returns 201.
- An edit that would duplicate another row returns 409 and changes nothing.
- A missing profile or item returns 404, including an item that belongs to another profile.
- Invalid input returns 422 and saves nothing.

Routes and rules are listed in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

**Matching test**

- `test_full_pantry_lifecycle` and the rest of `tests/test_api.py`
- `test_ui_and_api_see_each_others_writes` in `tests/test_ui_persistence.py`
