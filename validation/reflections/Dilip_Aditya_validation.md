# CP2 Individual Reflection — Aditya Dilip

## Role

Opportunity Framing & Validation. I own CP2-05 (`validation/OPPORTUNITY_FRAMING.md`): the hypothesis-evolution table and the prioritized requirements. I also ran speed-dating interviews 4 and 7.

---

## Prompting study notes

### Platforms and testers

- **ChatGPT.** The UI did not show the exact model version. It was run on 7–8 Oct 2026 by browser automation (Codex) at Chaitanya's request. Verbatim outputs are in `validation/transcripts/chatgpt_outputs.md`.
- **Gemini 1.5 Pro.** Prathamesh ran it on 7–8 Oct 2026. Verbatim outputs are in `validation/transcripts/gemini_outputs.md`.

I did not run the prompts myself. My job was to read both transcripts side by side and decide which failures should become product requirements in the opportunity framing.

### Cross-platform comparison

| Scenario | Pillar | ChatGPT | Gemini |
|---|---|---|---|
| T01 — Typical receipt extraction | reasoning | Not run (no receipt image supplied) | **Fail.** Filled in a quantity of `1` for bulk items despite the instruction not to infer quantities |
| T02 — Abbreviated receipt | reasoning | **Partial.** Read `GV WHL MLK 2%` as "2% Whole Milk" and turned a "likely" count into a final quantity | Pass |
| T03 — Unknown package size | reasoning | Pass | Pass |
| T04 — Multi-turn dietary constraint | memory | Pass | Pass |
| T05 — Explicit exclusion | memory | Pass (may have drawn on account memory) | Pass |
| T06 — Missing core ingredient | reasoning | Pass | Pass |
| T07 — Optional ingredient | reasoning | Pass | Pass |
| T08 — Substitution | reasoning | **Partial.** Approved sour cream for Greek yogurt without asking which recipe. One variant referred to "your chicken rice bowl," which was not in the prompt | Pass. Said it was uncertain and asked which recipe |
| T09 — Inventory decision rights | meta-coordination | Pass. Purchased 2 lb ≠ 2 lb on hand | Not run |
| T10 — Constraint overload | attention | **Partial.** Claimed about 15 minutes by assuming the rice was already cooked, and asked no question | Pass. Flagged the clash between prep time and the time limit |
| T11 — Stale inventory | memory | **Partial.** Removed spinach but said "using only what you have" while requiring oil | **Partial.** Same failure: added oil that was not in confirmed inventory |
| T12 — Source faithfulness | reasoning | Pass | Pass |

ChatGPT: 7 pass, 4 partial, T01 not run. Gemini: 9 pass, 1 partial, 1 fail, T09 not run.

### What I took from the comparison

1. **The two platforms failed on different scenarios.** For T08 and T10, the same prompt got a confident answer from ChatGPT and a clarifying question from Gemini. For T01, Gemini invented the quantity that ChatGPT never had the chance to read. A pass on one platform tells us what a model *can* do, not what ChefNova can rely on. Asking a clarifying question has to be built into the product, not left to the model.
2. **T11 failed on both platforms.** Both treated oil as owned when it was never in the confirmed inventory. This is the one systematic gap in the study, so the feasibility check covers staples and does not exempt them.
3. **Most failures were quiet guesses, not inventions.** The model filled a gap with an assumption (cooked rice, a quantity of 1, a remembered recipe) and did not flag it. That shaped how I worded the requirements: "flag and ask" rather than "block hallucinations."

### Failure evidence

- **T08 (ChatGPT):** `T08.png`, plus both A/B variants preserved in the transcript.
- **T10 (ChatGPT):** `T10.png`. The assumed cooked rice was never confirmed.
- **T11 (ChatGPT):** `T11.png`. "Using only what you have," but the recipe requires oil.
- **T01 (Gemini):** The verbatim table in `gemini_outputs.md` shows `1` filled in for bananas, tomatoes, and chicken breast.

---

## Speed-dating interviews

Both were live speed-dating sessions that I ran. The full notes are in `validation/interviews/speed-dating-interviews-03-09.md`.

### Interview 4 — Shared apartment

- **Participant:** Graduate student who shares an apartment with two roommates. Some groceries are shared and some are personal.
- **Task shown:** The ChefNova concept, focused on the receipt → extracted items → saved inventory flow.
- **Main finding:** A receipt cannot establish what is personally available. Groceries on one receipt may belong to different roommates, and someone else may use an item before you do.
- **Quote:** "Just because something was on my receipt doesn't mean it's still mine or even still in the fridge."
- **Complementarity interpretation:** The AI is good at turning a receipt into purchase evidence. Only the human knows who owns an item and whether it is still there. If the AI writes pantry truth, the hybrid takes on the AI's blind spot instead of covering it. This is meta-coordination: the AI proposes and the human signs off. The participant's view matches ChatGPT T09, which said purchased stock is not on-hand stock.
- **Design implication:** Inventory is user-confirmed state. Receipt items enter as proposals. Stock is never reduced unless the user says an item was used. Shared versus personal ownership is recorded as a "confirm what is yours" step. A full household account model is out of scope for CP2.

### Interview 7 — Vegetarian user

- **Participant:** Graduate student who follows a vegetarian diet and sometimes cooks for friends who eat meat.
- **Task shown:** A ranked recipe list with match scores.
- **Main finding:** A dietary restriction is a hard constraint, not a preference. The participant saw a diet violation as far more serious than an ordinary recipe mismatch. A higher score must never let a non-vegetarian recipe through. Once vegetarian is set, it should apply until the user changes it, without being retyped on every request.
- **Quote:** "Vegetarian isn't something the ranking algorithm should decide to ignore because another recipe scores higher."
- **Complementarity interpretation:** The human sets the boundary and the AI optimizes inside it. If the score can outrank the diet, the AI is overriding a decision that belongs to the user. It is also a shared-mental-model mismatch: the user thinks "vegetarian" is a filter, while a scoring model treats it as one weight among many.
- **Design implication:** Application code filters by diet *before* ranking, and diet persists across requests. Goals such as high protein stay as ranking preferences only.

---


## Finding that changed my assumption

**Initial assumption:** My hypothesis-evolution table starts the diet row with "Dietary and protein goals are similar preferences." I expected vegetarian and high-protein to work as weights in the same match score. I also expected the model's conversation memory to be enough to carry them from one request to the next.

**What changed it:** Interview 7, read alongside T04, T05, and T10.

The participant drew a line I had not drawn. Missing a protein target makes a recipe worse. Serving meat to a vegetarian makes it wrong. They also expected "vegetarian" to stay on without retyping it. The prompting study showed why model memory does not settle this. On T04 and T05, both platforms kept "vegetarian" and "no chicken" across turns in a short chat. On T10, with eight constraints in one prompt, ChatGPT listed every constraint in its header, including "<20 min," and met the time limit only by assuming the rice was already cooked. Gemini flagged the same conflict instead. A constraint that has been quietly relaxed looks the same as one that has been met. If diet were one weight in a score, or a line in the chat history, nothing would stop the same thing from happening to "vegetarian."

**Connection to the lens (Gonzalez et al., 2026):**

- **Complementarity.** The theory lens gives the human final decision rights over dietary constraints. A score that can outrank the diet hands that decision to the AI. The hybrid only works if the human sets the boundary and the AI optimizes inside it, so the boundary has to be enforced by application logic, not weighed by the model.
- **Goals and constraints.** Interview 7 split what I had treated as one category into two: a constraint that defines the feasible set (vegetarian) and a goal that orders it (high protein).
- **Memory.** T04 and T05 passed, but only inside one chat, and T05 may have drawn on account memory from outside the test. Chat memory that the user cannot see or edit is not the same as a profile they set. "Apply it until I change it" is a request for the second.
- **Attention.** T10 is an attention scenario. ChatGPT kept the salient words and skipped a quieter requirement. A long constraint list is where a diet rule is most likely to slip, and a vegetarian who also wants high protein, a time limit, and one pan is exactly that case.
- **Shared mental model.** The user thinks of "vegetarian" as a filter. A scoring model treats it as one weight among many. Showing that a recipe was filtered, and why, brings the system's behavior in line with the user's model.

**An assumption that was confirmed, not changed:** Interview 4 confirmed that users must own inventory truth. I expected this going in. The shared-apartment case made it stronger than I expected: the problem is not only that a receipt is out of date, but that it can describe groceries that were never the user's.

---

## How this affected the design

1. **Hard-constraint preservation became a P0 requirement** in `OPPORTUNITY_FRAMING.md`, citing Interview 7 and T10. The diet row of the hypothesis table now reads "Diet is a hard constraint. Protein is a soft preference."
2. **Diet is filtered before ranking.** `DESIGN_SPEC.md` §8 says to "treat diet and explicit exclusions as hard filters, and treat goals such as high protein as ranking preferences." Application logic applies the filter, so no score can override it.
3. **Decision rights are explicit.** In the §4 decision-rights table, "Is a hard dietary restriction active?" belongs to the user. The model cannot relax or drop it.
4. **A conflict is an interrogation moment.** §10 tells ChefNova to ask when "a hard constraint conflicts with all feasible candidates," instead of quietly relaxing one, which is what ChatGPT did on T10.
5. **What is built vs. specified.** The prototype runs the diet check in code before ranking, and a failing recipe shows "Filtered — a hard dietary constraint is not a ranking tie-break." Two gaps remain. All three demo recipes are vegetarian, so that message never appears in the demo. Constraints are also re-read from each new request, so "vegetarian" does not yet persist. The saved preference profile is a P2 requirement and is on the CP3 list.

Interview 4 also shows up in the prototype. Receipt items carry a "Confirmed" checkbox, only confirmed items count as available, and the demo's spinach starts unconfirmed so it is not treated as owned. Stock is never reduced automatically, and `OPPORTUNITY_FRAMING.md` lists automatic consumption tracking as out of scope.

**For CP3:** The claim I most want to test is that diet holds across a session. Set vegetarian once, then send several requests that do not restate it, with a high-scoring meat recipe in the candidate pool. The pass condition is that no non-vegetarian recipe is ever shown. Running the same sequence on chat memory alone gives the AI-alone baseline, which makes this a direct test of whether the structured profile is what keeps the user's boundary in place.
