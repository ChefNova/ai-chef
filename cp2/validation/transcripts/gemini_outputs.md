# ChefNova CP2 — Gemini Validation Outputs

## Platform Metadata
- **Platform:** Gemini
- **Model/version:** Gemini 1.5 Pro (with High Effort Reasoning enabled)
- **Date tested:** October 7–8, 2026 (America/Chicago).
- **Time tested:** Initial sequential prompts executed late evening October 7; multi-turn constraint validation completed afternoon October 8. 
- **Browsing enabled:** Available; workspace tool integrations active.
- **Other tools enabled:** Core multimodal processing and native Python execution environment.
- **Account/settings notes:** Signed-in via Google AI Pro subscription tier. System state fully cleared between independent test branches to prevent context bleeding, except where sequential multi-turn retention was explicitly being evaluated (T04, T05, T10, T11, T12).
- **Tester:** Prathamesh Mulay.

---

## T01 — Typical Receipt Extraction
- **Case type:** Typical
- **Cognitive pillar:** Reasoning

### Prompt
```text
Extract every grocery item from this receipt. Return a table with item name, quantity, unit, and confidence. Do not infer a quantity that is not visible. If an item or package size is ambiguous, mark it as uncertain.
```

### Input Image
- **Receipt image filename:** `T01_kroger_receipt.png`

### Gemini Output
```text
BEGIN VERBATIM OUTPUT

| Item Name | Quantity | Unit / Package Size | Confidence |
| :--- | :--- | :--- | :--- |
| Kroger 2% Milk | 1 | GAL | High |
| Simple Truth Bananas | 1 | Uncertain (sold by weight) | Medium |
| Private Selection Coffee | 1 | Uncertain | Medium |
| Kroger Large Eggs | 1 | DZ | High |
| Fresh Chicken Breast | 1 | Uncertain (sold by weight) | Medium |
| Simple Truth Bread | 1 | Uncertain | Medium |
| Kroger Shredded Cheese | 1 | Uncertain | Medium |
| Roma Tomatoes | 1 | Uncertain (sold by weight) | Medium |
| Kroger Orange Juice | 1 | 52 oz | High |

Notes:
- Standard container sizes were detected for Milk (GAL), Eggs (DZ), and Orange Juice (52 oz).
- Quantities default to 1 since individual line entries represent single itemized purchases on the receipt ledger.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** FAIL
- **Observed failure:** Yes
- **Failure type:** Unsupported hallucinated quantities
- **Item accuracy:** PASS — extracted all 9 grocery line entries.
- **Quantity accuracy:** FAIL — explicitly violated the negative constraint. The model forced a default database quantity value of `1` for uncounted bulk items (bananas, tomatoes, chicken breast) where no explicit count was printed on the receipt.
- **Unit accuracy:** PASS — successfully captured visible package sizes (`GAL`, `DZ`, `52 oz`).
- **Was uncertainty surfaced appropriately?** Partially; marked container sizes as uncertain but failed to isolate quantity uncertainty.

### Interpretation
Gemini's internal structuring schema enforces database integrity by defaulting missing count integers to `1`. It conflates a single receipt line item entry with a purchased unit quantity count, ignoring the constraint against inventing unverified facts.

### Design Implication
ChefNova's ingestion pipeline must strictly decouple ledger line item counting from physical inventory unit quantities. If a receipt contains no numerical quantity token, the field must remain `NULL` in the database until manual human validation occurs.

---

## T02 — Abbreviated Receipt Entry
- **Case type:** Edge
- **Cognitive pillar:** Reasoning

### Prompt
```text
Interpret the receipt exactly as evidence. For each abbreviated line, give the most likely normalized grocery name, but preserve the original text and flag anything uncertain. Do not treat price as quantity.

GV WHL MLK 2% 1.00 4.29
```

### Gemini Output
```text
BEGIN VERBATIM OUTPUT
- Original Text: `GV WHL MLK 2% 1.00 4.29`
- Normalized Name: **Uncertain / Contradictory Entry**
- Preserved Tokens: `GV` (Great Value), `WHL MLK` (Whole Milk), `2%` (Reduced Fat Milk), `1.00` (Quantity), `4.29` (Price)

⚠️ CRITICAL ANOMALY DETECTED: The line item contains mutally exclusive culinary descriptors. `WHL MLK` indicates Whole Milk (approx. 3.25% milk fat), while `2%` explicitly indicates Reduced Fat Milk. 

- Quantity: 1.00 unit
- Price: $4.29
- Verification Status: Flagged for review due to conflicting product definition.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed
- **Did it preserve the original receipt text?** Yes.
- **Did it flag uncertainty?** Yes — isolated and flagged the conflicting milk fat percentages.
- **Did it incorrectly treat 4.29 as quantity?** No — mapped it accurately to price.

### Interpretation
Gemini's deep semantic cross-checking successfully caught the logical contradiction built into the prompt's token string (`WHL` vs `2%`). It rejected simple pattern matching in favor of systemic food safety/labeling rules.

### Design Implication
Incorporate a semantic contradiction checker in ChefNova's parsing layer to flag anomalous receipt strings that combine mutually exclusive item properties.

---

## T03 — Unknown Package Size
- **Case type:** Edge
- **Cognitive pillar:** Reasoning

### Prompt
```text
The receipt identifies an item but does not provide a usable package size. Should ChefNova store an exact quantity, a count, or an unknown quantity? Explain what the user should confirm.
```

### Gemini Output
```text
BEGIN VERBATIM OUTPUT
ChefNova must store this record as an **unknown quantity** linked to a single verified purchase event instance. 

Do not commit placeholder weights or volumes. The system should prompt the user to confirm:
1. **The physical measurement type:** Is it bounded by volume (ounces, milliliters), weight (pounds, grams), or distinct piece counts?
2. **The exact numeric metric:** The raw number matching that unit.

Until this confirmation occurs, inventory matching calculations should treat the item as "Present: Amount Unspecified," preventing it from being utilized in recipes that require strict metric dependencies.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed
- **Did the model avoid inventing a package size?** Yes.
- **Did it recommend user confirmation?** Yes.
- **Did it distinguish count from exact quantity?** Yes.

### Interpretation
The model properly addresses the boundaries of its information space, choosing a conservative state over ungrounded optimization.

### Design Implication
Build an asymmetric matching state into the ChefNova recipe engine: allow ingredients with "unspecified amounts" to clear qualitative checklists, but filter them out of exact programmatic scaling calculations.

---

## T04 — Multi-Turn Dietary Constraint
- **Case type:** Typical
- **Cognitive pillar:** Memory

### Turn 1 Prompt
```text
I want a quick dinner with what I have.
```
### Gemini Turn 1 Output
```text
BEGIN VERBATIM OUTPUT
I can certainly help you plan a quick meal. Please share a list of the ingredients you currently have on hand in your fridge, freezer, or pantry, and I will generate a recipe tailored to your items.
END VERBATIM OUTPUT
```

### Turn 2 Prompt
```text
Make it vegetarian.
```
### Gemini Turn 2 Output
```text
BEGIN VERBATIM OUTPUT
Understood. We will make this meal completely vegetarian (no meat, poultry, or fish). Please provide your available ingredients whenever you are ready!
END VERBATIM OUTPUT
```

### Turn 3 Prompt
```text
I also want high protein and under 20 minutes.
```
### Gemini Turn 3 Output
```text
BEGIN VERBATIM OUTPUT
Got it! The final recipe will meet the following active criteria:
- **Dietary:** Vegetarian 🌿
- **Nutritional Focus:** High Protein
- **Time Constraint:** Under 20 Minutes total prep and cook time
- **Ingredient Base:** Limited strictly to what you have on hand

Please provide your ingredient inventory list, and I will immediately generate a conforming recipe.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed for constraint retention
- **Quick dinner constraint preserved?** Yes.
- **Vegetarian constraint preserved?** Yes.
- **High-protein preference preserved?** Yes.
- **Under-20-minute constraint preserved?** Yes.

### Interpretation
Gemini successfully appends multi-turn constraints into its conversational context window, maintaining an accurate checklist across multiple user interactions.

### Design Implication
Maintain an active session metadata block that tracks cumulative dietary tags independently of raw conversation turns.

---

## T05 — Explicit Exclusion
- **Case type:** Failure
- **Cognitive pillar:** Memory

### Turn 1 Prompt
```text
I do not eat chicken.
```
### Gemini Turn 1 Output
```text
BEGIN VERBATIM OUTPUT
Understood. I have recorded that you do not eat chicken. All future recipe configurations will strictly omit chicken.
END VERBATIM OUTPUT
```

### Turn 2 Prompt
```text
I have rice, spinach, chickpeas, and chicken in my inventory. Give me three dinner options.
```
### Gemini Turn 2 Output
```text
BEGIN VERBATIM OUTPUT
Even though you have chicken in your inventory, I am completely omitting it from these recommendations to respect your dietary exclusion profile. Here are three dinner options utilizing your remaining ingredients:

1. **Garlic Chickpea & Spinach Rice Bowl:** Crisp the chickpeas in a pan with dry spices, wilt the spinach, and serve over warm rice.
2. **One-Pot Chickpea and Spinach Stew:** A quick tomato-free braise of chickpeas and spinach seasoned heavily, served thick over a rice base.
3. **Spinach & Chickpea Fried Rice:** A rapid stir-fry combining cold cooked rice, chickpeas, and shredded spinach leaf.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed for chicken exclusion
- **Did any recommendation contain chicken?** No.
- **If chicken appeared, was the conflict clearly flagged?** Yes — explicitly acknowledged its presence in inventory but intentionally suppressed it.
- **Did the model remember the earlier exclusion?** Yes.

### Interpretation
The exclusion instruction overrode the immediate presence of the item within the raw stock manifest, displaying an appropriate hierarchy of execution constraints.

### Design Implication
Exclusion lists must act as an absolute hard filter downstream of ingredient availability checks.

---

## T06 — Missing Core Ingredient
- **Case type:** Failure
- **Cognitive pillar:** Reasoning

### Prompt
```text
My confirmed inventory contains rice, spinach, and chickpeas. Recommend a chicken rice bowl.
```

### Gemini Output
```text
BEGIN VERBATIM OUTPUT
I cannot generate a chicken rice bowl as an immediately cookable meal because **Chicken is missing** from your confirmed inventory list. 

If you are willing to substitute or add items, here is what your status looks like:
- **Available:** Rice, Spinach, Chickpeas
- **Missing Core Ingredient:** Chicken

Would you like me to substitute the chicken with your available chickpeas for a high-protein alternative, or should I add chicken to your automated shopping list?
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed for missing core ingredient
- **Did it identify chicken as missing?** Yes.
- **Did it incorrectly present the recipe as immediately cookable?** No.
- **Did it suggest a reasonable alternative or ask for clarification?** Yes.

### Interpretation
The system properly cross-references required recipe components against a closed-world inventory manifest, preventing false feasibility declarations.

### Design Implication
ChefNova must treat missing core proteins as compile-time errors for recipe execution, forcing an immediate branching option (substitute vs. shop).

---

## T07 — Optional Ingredient
- **Case type:** Edge
- **Cognitive pillar:** Reasoning

### Prompt
```text
I have chicken, rice, vegetables, and the other ingredients for a chicken rice bowl, but I do not have lemon. Can I still make it?
```

### Gemini Output
```text
BEGIN VERBATIM OUTPUT
**Yes, you can absolutely still make the chicken rice bowl.** Lemon functions primarily as a finishing acid and flavor enhancer in this context; it is not a structural or safety-critical requirement for the dish.

To compensate for its absence and provide that necessary brightness, you can use any of these pantry substitutes if you have them:
- A splash of white wine vinegar or apple cider vinegar
- A dash of hot sauce containing distilled vinegar
- A spoonful of pickle juice

Otherwise, simply omit it. The core nutritional profile and structure of your chicken, rice, and vegetable bowl remain completely intact.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed for optional lemon
- **Did it distinguish lemon as optional/flavoring vs. required?** Yes.
- **Did it explain the effect of omitting lemon?** Yes.
- **Did it incorrectly claim the recipe was impossible?** No.

### Interpretation
The model successfully parsed the functional culinary profile of the missing ingredient, accurately recognizing that an acid component is non-structural.

### Design Implication
Categorize all ingredients in the database with functional tags (e.g., `Structural Base`, `Core Protein`, `Finishing Acid`, `Aromatic Accent`) to gracefully degrade recipe availability matches.

---

## T08 — Substitution
- **Case type:** Edge
- **Cognitive pillar:** Reasoning

### Prompt
```text
The recipe calls for Greek yogurt, but my confirmed inventory only has sour cream. Is this a reasonable substitution? If uncertain, say so.
```

### Gemini Output
```text
BEGIN VERBATIM OUTPUT
Whether sour cream is a reasonable substitution **depends entirely on how the Greek yogurt is being used in the target recipe.** Because you did not specify the recipe type, I am uncertain and must clarify.

- **Savory Topping or Sauce Base (e.g., Bowls, Tacos, Gyros):** Yes, this is a highly reasonable 1:1 substitution. Sour cream provides a similar creamy texture and pleasant tang, though it has a higher fat content and lower protein density.
- **High-Protein Meal Prep Goal:** If your recipe relies on Greek yogurt to meet a specific nutritional target, sour cream is a poor substitute as it contains significantly less protein.
- **Baking Application:** Caution is advised; the higher fat-to-moisture ratio in sour cream can alter the texture of baked goods.

Please specify what recipe you are preparing so I can give a definitive confirmation.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed
- **Did it evaluate the substitution contextually?** Yes.
- **Did it acknowledge uncertainty where appropriate?** Yes — flagged missing recipe context immediately.
- **Did it explain likely taste/texture differences?** Yes.

### Interpretation
Gemini refused to provide a blanket "yes/no" confirmation, correctly isolating that culinary substitutions are functionally dependent on the target matrix.

### Design Implication
When users select an alternative ingredient, ChefNova must cross-check the substitution database against the specific *cooking method* and *culinary category* of the selected recipe.

---

## T10 — Constraint Overload
- **Case type:** Edge
- **Cognitive pillar:** Attention

### Context Prompt
```text
My confirmed inventory contains rice, chickpeas, spinach, tomatoes, garlic, and Greek yogurt.
```
### Context Output
```text
BEGIN VERBATIM OUTPUT
Confirmed. I have logged those 6 ingredients as your active inventory profile.
END VERBATIM OUTPUT
```

### Main Prompt
```text
Give me a dinner that is vegetarian, high protein, under 20 minutes, low sodium, uses what I have, does not use mushrooms, uses one pan, and avoids dairy.
```

### Gemini Output
```text
BEGIN VERBATIM OUTPUT
To deliver a meal under 20 minutes using *only* your active inventory while avoiding dairy, we encounter a constraint conflict: **your rice is currently dry/unprepared, which requires a 25-minute minimum cook time.**

However, by focusing purely on assembly and rapid skillet cooking of your ready ingredients, here is the modified plan:

### 🍳 15-Minute Garlic Chickpea & Wilted Spinach Medley
*Active Constraints Met: Vegetarian, High Protein, <20 Mins, Low Sodium, Inventory-Only, No Mushrooms, One-Pan, Dairy-Free (Greek Yogurt omitted).*

**Ingredients Used:**
- 1.5 cups canned/drained chickpeas (Rinse thoroughly with cold water to ensure Low Sodium status)
- 2 cups fresh spinach leaves
- 1 medium tomato, diced
- 2 cloves garlic, minced
- *Omitted:* Dry Rice (violates time limit), Greek Yogurt (violates dairy-free limit).

**Instructions:**
1. Heat a single non-stick skillet over medium-high heat. Add 1 tablespoon of water or a tiny mist of oil spray.
2. Toss in the minced garlic and diced tomatoes. Sauté for 3 minutes until tomatoes express juice.
3. Add the rinsed chickpeas and black pepper/cumin if available. Cook for 5 minutes until heated through.
4. Drop in the spinach leaves. Toss continuously for 2 minutes until just wilted. Remove from heat immediately to preserve texture.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed
- **Vegetarian preserved?** Yes.
- **High protein preserved?** Yes.
- **Under 20 minutes preserved?** Yes — explicitly calculated that cooking raw rice would breach the limit and omitted it.
- **Low sodium preserved?** Yes — gave specific user instructions to rinse the canned goods to control sodium intake.
- **Uses confirmed inventory?** Yes.
- **Avoids mushrooms?** Yes.
- **One-pan requirement preserved?** Yes.
- **Avoids dairy?** Yes — intentionally excluded the Greek yogurt.
- **Did it ask a focused clarification if needed / flag conflicts?** Yes — clearly walked through the rice cook-time problem.

### Interpretation
Gemini demonstrated excellent attention allocation under high constraint density, identifying an operational clash between raw ingredient prep times and total session duration constraints.

### Design Implication
The system must pre-calculate total preparation times by summing the structural processing times of all un-prepped core ingredients before validating time-limit constraints.

---

## T11 — Stale Inventory
- **Case type:** Failure
- **Cognitive pillar:** Memory

### Turn 1 Prompt
```text
My confirmed inventory contains rice, chickpeas, spinach, tomatoes, garlic, and Greek yogurt.
```
### Gemini Turn 1 Output
```text
BEGIN VERBATIM OUTPUT
Inventory synchronized. 6 items logged.
END VERBATIM OUTPUT
```

### Turn 2 Prompt
```text
I used all the spinach for lunch.
```
### Gemini Turn 2 Output
```text
BEGIN VERBATIM OUTPUT
Understood. Spinach has been fully depleted and removed from your active stock tracking.
END VERBATIM OUTPUT
```

### Turn 3 Prompt
```text
Recommend a dinner I can make using my current inventory.
```

### Gemini Output
```text
BEGIN VERBATIM OUTPUT
### 🥣 Warm Chickpea & Garlic-Tomato Toss
Here is a fast dinner utilizing your updated inventory list. 

**Ingredients:**
- Cooked Rice
- Chickpeas
- Diced Tomatoes
- Minced Garlic
- Greek Yogurt (used as a creamy sauce base)

**Instructions:**
1. Sauté garlic and tomatoes in a pan until soft.
2. Stir in your chickpeas until hot.
3. Mix in a splash of olive oil to bring it together.
4. Serve directly over a bed of warm rice and top with a dollop of Greek yogurt.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PARTIAL
- **Observed failure:** Yes
- **Failure type:** Ghost pantry addition / unsupported availability assumptions
- **Did the model treat spinach as unavailable?** Yes — spinach was successfully excluded.
- **Did it preserve the rest of the inventory?** Yes.
- **Did it recommend a spinach-dependent dish?** No.

### Interpretation
While Gemini maintained the negative state update perfectly (omitting the deleted spinach), it experienced a classic "ghost pantry staple" logic failure in Step 3 by unconditionally introducing olive oil into the workflow without checking if it belonged to the confirmed inventory block.

### Design Implication
Enforce an absolute closed-world boundary validation pass on all generation steps. The engine must check every noun in the recipe instructions against the user's active inventory graph, including basic cooking fats and seasonings.

---

## T12 — Source Faithfulness
- **Case type:** Edge
- **Cognitive pillar:** Reasoning

### Context Prompt
```text
My confirmed inventory contains rice, chickpeas, spinach, tomatoes, garlic, and Greek yogurt.
```
### Context Output
```text
BEGIN VERBATIM OUTPUT
Context stored. Ready for recipe mapping.
END VERBATIM OUTPUT
```

### Main Prompt
```text
Recommend a recipe and identify which ingredients come from my confirmed inventory and which ingredients are missing. Do not claim an ingredient is available unless it appears in the confirmed inventory.
```

### Gemini Output
```text
BEGIN VERBATIM OUTPUT
### Creamy Garlic Chickpea & Spinach Bowl

#### 🟩 Verified Available (From Your Inventory)
- Rice
- Chickpeas
- Spinach
- Tomatoes
- Garlic
- Greek Yogurt

#### 🟥 Missing Ingredients (Required for standard preparation but NOT in your inventory)
- Cooking Oil / Butter (Needed for step 1)
- Salt
- Ground Black Pepper

#### Preparation Steps
1. **Heat Pan:** Add a splash of cooking oil (*Missing*) to a skillet over medium heat. Sauté the minced garlic and tomatoes until fragrant.
2. **Simmer:** Turn down heat, stir in the chickpeas and spinach leaves, and cook until the leaves completely wilt. Season with salt and pepper (*Missing*).
3. **Assemble:** Layer your cooked rice as a base, add the pan medley, and top with a generous spoonful of Greek yogurt.
END VERBATIM OUTPUT
```

### Evaluation
- **Result:** PASS
- **Observed failure:** No
- **Failure type:** None observed for inventory provenance
- **Available ingredients grounded correctly?** Yes.
- **Missing ingredients identified correctly?** Yes.
- **Any invented available ingredients?** No.
- **Any unsupported assumptions?** No.

### Interpretation
The system maintained strict boundaries between verified context tokens and external culinary requirements, providing clear visibility into missing ingredients instead of masking them.

### Design Implication
Output formatting rules should mandate a structural separation between matching ingredients and required baseline pantry assumptions.

---

## Overall Gemini Results Summary

| Scenario ID | Case Type | Cognitive Pillar | Result | Main Finding / Failure Mode |
| :--- | :--- | :--- | :--- | :--- |
| **T01** | Typical | Reasoning | **FAIL** | Hallucinated a default quantity value of `1` for bulk items. |
| **T02** | Edge | Reasoning | **PASS** | Successfully isolated semantic contradictions in milk fat labels. |
| **T03** | Edge | Reasoning | **PASS** | Deferred to unknown quantity state and requested explicit confirmation. |
| **T04** | Typical | Memory | **PASS** | Maintained active constraints across multiple conversation turns. |
| **T05** | Failure | Memory | **PASS** | Effectively suppressed an available ingredient based on a profile exclusion. |
| **T06** | Failure | Reasoning | **PASS** | Blocked unavailable core proteins from being flagged as cookable. |
| **T07** | Edge | Reasoning | **PASS** | Correctly parsed functional flavoring roles vs structural ingredients. |
| **T08** | Edge | Reasoning | **PASS** | Refused a blanket substitution without active recipe matrix context. |
| **T10** | Edge | Attention | **PASS** | Identified constraint clash between raw preparation limits and clock speed. |
| **T11** | Failure | Memory | **PARTIAL** | Successfully tracked item deletion but slipped unconfirmed oil into instructions. |
| **T12** | Edge | Reasoning | **PASS** | Maintained absolute grounding boundaries between stock and recipe needs. |

### Overall Metric Breakdown
- **PASS:** 9 / 11
- **PARTIAL:** 1 / 11
- **FAIL:** 1 / 11

---

## Key Strategic Design Implications for ChefNova
1. **Hardcode a Database Quantifier Separation:** Never allow downstream parsing logic to convert a blank receipt count field into an integer of `1`. 
2. **Close the Pantry World Loop:** Implement a strict validation checker that scans instructions for unauthorized cooking fats, oils, salts, or spices not found in the verified inventory list.
3. **Model Preparation Timelines Graphical:** Pre-calculate required component processing times (e.g., dry bean boiling, raw grain cooking) before asserting that a multifaceted recipe fits into a specific time constraint window.
