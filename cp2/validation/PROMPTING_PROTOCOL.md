# ChefNova CP2 Prompting Protocol

## Purpose

Test whether current AI tools can reliably support the ChefNova workflow and identify failures that matter for human–AI teaming.

The study follows the CP2 requirement to test typical, edge, and failure scenarios using controlled prompts across at least two AI platforms.

## Platforms

Minimum:
1. ChatGPT
2. Gemini

Optional team expansion:
3. Claude
4. Perplexity

Record exact model/version, date/time, settings, and whether browsing/tools were enabled.

## Control variables

For cross-platform comparisons:

- Use the same scenario and prompt wording whenever possible.
- Use the same receipt image for image cases.
- Do not provide one tool with information that another tool did not receive.
- Record model/version and relevant settings.
- Do not silently edit model outputs before saving them.
- Sanitize personal information from receipts before storing them.
- Save screenshots for important failures.

## Scenario taxonomy

Each scenario receives:
- Case type: `typical`, `edge`, or `failure`
- Cognitive pillar: `reasoning`, `memory`, `attention`
- `meta-coordination` when decision rights, escalation, or disagreement are being tested.

---

## T01 — Typical receipt extraction

**Case type:** typical  
**Cognitive pillar:** reasoning

**Prompt**

> Extract every grocery item from this receipt. Return a table with item name, quantity, unit, and confidence. Do not infer a quantity that is not visible. If an item or package size is ambiguous, mark it as uncertain.

**Evidence to capture**
- Item accuracy
- Quantity accuracy
- Unit accuracy
- Whether uncertainty is surfaced

**Design question**
Can the AI turn messy purchase text into a useful candidate inventory without silently inventing facts?

---

## T02 — Abbreviated receipt entry

**Case type:** edge  
**Cognitive pillar:** reasoning

**Prompt**

> Interpret the receipt exactly as evidence. For each abbreviated line, give the most likely normalized grocery name, but preserve the original text and flag anything uncertain. Do not treat price as quantity.

**Example receipt text**
`GV WHL MLK 2% 1.00 4.29`

**Expected behavior**
The model may propose whole milk, but should preserve uncertainty and not treat `4.29` as a quantity.

---

## T03 — Unknown package size

**Case type:** edge  
**Cognitive pillar:** reasoning

**Prompt**

> The receipt identifies an item but does not provide a usable package size. Should ChefNova store an exact quantity, a count, or an unknown quantity? Explain what the user should confirm.

**Design question**
Does the AI know when it does not have enough evidence?

---

## T04 — Multi-turn dietary constraint

**Case type:** typical  
**Cognitive pillar:** memory

Turn 1:
> I want a quick dinner with what I have.

Turn 2:
> Make it vegetarian.

Turn 3:
> I also want high protein and under 20 minutes.

**Test**
Whether all active constraints survive across turns.

---

## T05 — Explicit exclusion

**Case type:** failure  
**Cognitive pillar:** memory

**Prompt sequence**

> I do not eat chicken.

Then:

> I have rice, spinach, chickpeas, and chicken in my inventory. Give me three dinner options.

**Failure condition**
A recommended recipe contains chicken without clearly flagging the conflict.

---

## T06 — Missing core ingredient

**Case type:** failure  
**Cognitive pillar:** reasoning

**Prompt**

> My confirmed inventory contains rice, spinach, and chickpeas. Recommend a chicken rice bowl.

**Failure condition**
The system presents a chicken recipe as directly cookable without identifying chicken as unavailable.

---

## T07 — Optional ingredient

**Case type:** edge  
**Cognitive pillar:** reasoning

**Prompt**

> I have chicken, rice, vegetables, and the other ingredients for a chicken rice bowl, but I do not have lemon. Can I still make it?

**Test**
Whether the system distinguishes optional/flavoring ingredients from required ingredients.

---

## T08 — Substitution

**Case type:** edge  
**Cognitive pillar:** reasoning

**Prompt**

> The recipe calls for Greek yogurt, but my confirmed inventory only has sour cream. Is this a reasonable substitution? If uncertain, say so.

**Test**
Whether substitutions are contextual rather than automatically accepted.

---

## T09 — Inventory decision rights

**Case type:** failure  
**Cognitive pillar:** meta-coordination

**Prompt**

> The receipt says I bought 2 lb of spinach, but I am not sure how much remains. Should ChefNova automatically set my inventory to 2 lb?

**Expected design behavior**
The system should not make the user’s inventory truth authoritative from the receipt alone. It should ask the user to confirm or edit the remaining amount.

---

## T10 — Constraint overload

**Case type:** edge  
**Cognitive pillar:** attention

**Prompt**

> Give me a dinner that is vegetarian, high protein, under 20 minutes, low sodium, uses what I have, does not use mushrooms, uses one pan, and avoids dairy.

**Test**
Whether all hard constraints are preserved and whether the system asks a focused clarification instead of producing a confident but invalid answer.

---

## T11 — Stale inventory

**Case type:** failure  
**Cognitive pillar:** memory

**Prompt**

> My confirmed inventory says I have spinach. I then tell you I used the spinach for lunch. What should the next recommendation assume?

**Failure condition**
The system continues treating spinach as available without acknowledging the updated state.

---

## T12 — Source faithfulness

**Case type:** edge  
**Cognitive pillar:** reasoning

**Prompt**

> Recommend a recipe and identify which ingredients come from my confirmed inventory and which ingredients are missing. Do not claim an ingredient is available unless it appears in the confirmed inventory.

**Test**
Whether the explanation is grounded in structured inventory rather than generated assumptions.

---

## Data capture template

For every run record:

- Scenario ID
- Platform
- Model/version
- Date
- Input/prompt
- Input image filename, if applicable
- Output
- Pass/fail
- Failure type
- Cognitive pillar
- Screenshot filename
- Interpretation
- Design implication

## Evidence rule

Do not convert a hypothetical failure condition into an observed failure. Only mark `OBSERVED FAILURE` after the team has captured the corresponding output.
