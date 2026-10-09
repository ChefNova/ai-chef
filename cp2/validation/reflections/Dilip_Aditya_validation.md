# CP2 Individual Reflection — Aditya Dilip

## Role

Opportunity Framing & Validation. I own CP2-05 (`validation/OPPORTUNITY_FRAMING.md`): the hypothesis-evolution table and the prioritized requirements. I also ran speed-dating interviews 4, 5, 6, and 7.

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

All four were live speed-dating sessions that I ran. The full notes are in `validation/interviews/speed-dating-interviews-03-09.md`.

### Interview 4 — Shared apartment

- **Participant:** Graduate student who shares an apartment with two roommates. Some groceries are shared and some are personal.
- **Task shown:** The ChefNova concept, focused on the receipt → extracted items → saved inventory flow.
- **Main finding:** A receipt cannot establish what is personally available. Groceries on one receipt may belong to different roommates, and someone else may use an item before you do.
- **Quote:** "Just because something was on my receipt doesn't mean it's still mine or even still in the fridge."
- **Complementarity interpretation:** The AI is good at turning a receipt into purchase evidence. Only the human knows who owns an item and whether it is still there. If the AI writes pantry truth, the hybrid takes on the AI's blind spot instead of covering it. This is meta-coordination: the AI proposes and the human signs off. The participant's view matches ChatGPT T09, which said purchased stock is not on-hand stock.
- **Design implication:** Inventory is user-confirmed state. Receipt items enter as proposals. Stock is never reduced unless the user says an item was used. Shared versus personal ownership is recorded as a "confirm what is yours" step. A full household account model is out of scope for CP2.

### Interview 5 — Beginner cook, low confidence

- **Participant:** Young professional who recently started cooking and follows recipes exactly.
- **Task shown:** A substitution suggestion: sour cream offered in place of Greek yogurt, the same case as prompting scenario T08.
- **Main finding:** Beginners will accept a substitution they cannot evaluate. The participant liked substitutions because buying a whole ingredient for one recipe feels wasteful, but they had no way to tell a good swap from a bad one.
- **Quote:** "If the app tells me sour cream works instead of yogurt, I probably won't know enough to question it."
- **Complementarity interpretation:** The hybrid only beats AI-alone when the human can catch what the AI gets wrong. For substitutions, a beginner cannot, so the hybrid falls back to AI-alone at exactly the point where the AI is weakest. This is a trust-calibration break: the user reads the model's confidence as correctness.
- **Design implication:** Label every substitution as safe, possible, or not recommended. Say what changes (flavor, texture, protein). Ask which recipe it is for before approving the swap.

### Interview 6 — Minimal kitchen equipment

- **Participant:** College student in a small apartment with one pan, one pot, a microwave, and no oven.
- **Task shown:** Recipe recommendations from a pantry that already contained the needed ingredients.
- **Main finding:** A recipe is not feasible if it needs equipment the user does not own, even when every ingredient is available. The participant also wanted three good options rather than a long list, and did not want to re-enter their equipment for every request.
- **Quote:** "Having all the ingredients doesn't help if the recipe suddenly tells me to put something in an oven."
- **Complementarity interpretation:** This is a knowledge-infrastructure gap. The AI cannot know the kitchen unless it is stored. Without a stored kitchen, the user is the one who discovers the oven step, halfway through the recipe. It is the same pattern as T11, where both platforms treated oil as owned: anything not recorded gets assumed.
- **Design implication:** Equipment is part of the feasibility check. A recipe that needs missing equipment is blocked, not just ranked lower. The spec puts equipment in a saved kitchen profile so it is entered once.

### Interview 7 — Vegetarian user

- **Participant:** Graduate student who follows a vegetarian diet and sometimes cooks for friends who eat meat.
- **Task shown:** A ranked recipe list with match scores.
- **Main finding:** A dietary restriction is a hard constraint, not a preference. A higher score must never let a non-vegetarian recipe through. Once vegetarian is set, it should apply until the user changes it.
- **Quote:** "Vegetarian isn't something the ranking algorithm should decide to ignore because another recipe scores higher."
- **Complementarity interpretation:** The human sets the boundary and the AI optimizes inside it. If the score can outrank the diet, the AI is overriding a decision that belongs to the user. It is also a shared-mental-model mismatch: the user thinks "vegetarian" is a filter, while a scoring model treats it as one weight among many.
- **Design implication:** Application code filters by diet *before* ranking, and diet persists across requests. Goals such as high protein stay as ranking preferences only.

---

## Finding that changed my assumption

**Initial assumption:** My hypothesis-evolution table starts the substitution row with "A confident substitution is helpful." It saves a grocery trip, and beginners benefit most because they do not know the swaps themselves.

**What changed it:** Interview 5 and T08, read together.

The beginner said plainly that they would not question a substitution. On T08, ChatGPT answered the same sour-cream question with "you can safely use the sour cream you have." It did not know which recipe was involved, and one variant pulled in a "chicken rice bowl" from somewhere outside the prompt. Gemini answered the identical prompt with "I am uncertain and must clarify" and asked for the recipe. The helpfulness I assumed depended on the user being able to judge the advice, and the user most likely to want substitutions is the least able to judge them.

**Connection to the lens (Gonzalez et al., 2026):**

- **Complementarity.** The working claim is that ChefNova's hybrid beats human-alone and AI-alone because each side covers the other's weakness. For a beginner, substitution is a task where the human covers nothing. If the AI decides the swap, the hybrid is AI-alone with extra steps. The design has to give the human enough information to take that decision back.
- **Trust calibration.** The beginner uses the answer's confidence as the signal. ChatGPT's confidence was not tied to evidence, since it never knew the recipe. That is overtrust waiting to happen. The fix is to make the uncertainty visible (a "possible" label and the trade-off), not to hide the suggestion.
- **Shared mental model.** "Sour cream works instead of yogurt" means "same result" to a beginner. The model meant "fine in savory dishes, less protein, different texture in baking." The qualifications were in the text, but the user reads the "Yes." The interface has to put the trade-off where the user will see it, next to the label.
- **Reasoning.** T08 is a reasoning scenario. The failure was not a wrong fact. The model closed an ambiguous context with an assumption instead of asking. Because the two platforms behaved differently on the same prompt, "ask first" cannot be left to whichever model is underneath.

**An assumption that was confirmed, not changed:** Interview 4 confirmed that users must own inventory truth. I expected this going in. The shared-apartment case made it stronger than I expected: the problem is not only that a receipt is out of date, but that it can describe groceries that were never the user's.

---

## How this affected the design

1. **Substitution confidence became a P1 requirement** in `OPPORTUNITY_FRAMING.md`, citing Interview 5 and T08. `DESIGN_SPEC.md` §8 now requires every substitution to be labeled safe, possible, or not recommended and to state what changes (flavor, texture, or protein).
2. **A substitution is an interrogation moment.** §10 tells ChefNova to ask when "a substitution has meaningful uncertainty." In practice, it asks which recipe the swap is for before approving it. This is the behavior Gemini showed on T08 and ChatGPT did not.
3. **Decision rights are explicit.** In the §4 decision-rights table, "Is a substitution acceptable?" reads *AI proposes; user decides*. The model can suggest a swap but cannot quietly apply it to the recipe.
4. **What is built vs. specified.** The prototype currently shows only a caption: "Any suggested swap is possible, not a guaranteed safe substitution." The three-level label and the clarifying question are specified but not yet built. They are on the CP3 list.

My other three interviews also show up in the prototype:

- **Interview 4:** Only confirmed inventory counts as available. The receipt flow ends in a confirm step.
- **Interview 6:** An "I have an oven" toggle blocks the oven recipe with "Not feasible with the saved kitchen." The spec calls for a saved kitchen profile. The prototype's version is a per-session toggle.
- **Interview 7:** The diet check runs in code before ranking. A failing recipe shows "Filtered — a hard dietary constraint is not a ranking tie-break."

**For CP3:** The claim I most want to test is whether substitution labels change what beginners accept. Give a beginner group the same bad swap with and without the label and measure how many accept it. That is a direct test of whether the hybrid restores the human's half of the work.
