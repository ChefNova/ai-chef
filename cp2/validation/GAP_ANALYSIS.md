# ChefNova CP2 Gap Analysis

## Purpose

This matrix connects CP2 evidence to the human–AI teaming lens and then to concrete ChefNova design decisions. The required reasoning chain is:

**Receipt → Theory → Design**

The theoretical interpretation is based on Gonzalez et al. (2026), *Toward a science of human–AI teaming for decision making: A complementarity framework*.

## Evidence used

- ChatGPT transcript: `validation/transcripts/chatgpt_outputs.md` (GPT 5.6 Sol, 7–8 Oct 2026). 8 pass, 4 partial, 0 fail.
- Interview 1, phone: `validation/interviews/pilot-interview-01.md`. Interviewer not named.
- Interviews 3–9: `validation/interviews/simulated-interviews-03-09.md`. These were supplied as simulated notes, not live speed-dating transcripts.
- Interview 2 was not supplied.
- Gemini outputs are still the placeholder in `validation/transcripts/gemini_outputs.md`.

## Cross-cutting gap matrix

| Dimension | Empirical receipt | Theoretical reading | ChefNova design response |
|---|---|---|---|
| Accuracy | Interview 1 will not trust automatic adds from abbreviated receipts or non-food lines. Simulated interview 4: a receipt can mix roommates' groceries. ChatGPT T02 turned `GV WHL MLK 2%` into “2% Whole Milk” and promoted a “likely” count to a final quantity. | Reasoning fails when the model closes an ambiguous parse. That is a knowledge-infrastructure gap if the raw line is discarded. | Keep the raw receipt text, flag conflicting descriptors, and require review before confirm. |
| Reliability | Simulated interview 3: “under 20 minutes” is strict. Simulated interview 7: vegetarian must not be dropped because another recipe scores higher. ChatGPT T10 claimed about 15 minutes while assuming cooked rice. | A shared mental model breaks when a stated limit is treated as a soft hint. | Diet, time, and explicit exclusions are hard filters. Application logic enforces them before ranking. |
| Memory | Interview 1: spinach marked unavailable must stay out of later recipes. Simulated interview 9: one constraint in a stack must not disappear. ChatGPT T04 and T05 retained constraints in-chat. T11 removed spinach, then still required oil under “using only what you have.” T05 also imported preferences that the prompt did not state. | Remembering one update is not the same as a shared inventory model. Account memory is not the application's memory. | Persist inventory, hard preferences, and equipment in structured state. Session remarks do not rewrite the saved pantry. |
| UX friction | Interview 1: hand-updating every consumed item could cost more effort than recipe search. Simulated interview 3 wants “rice, eggs, spinach” without units. Simulated interview 6 does not want to re-enter equipment. Simulated interview 9 does not want to retype six preferences. | Attention orchestration fails when the user must repeat state the system should already hold. | Receipt, text, and voice entry. A saved kitchen profile and saved hard constraints. Ask one question only when constraints conflict. |
| Safety | Simulated interview 7 treats a dietary miss as more serious than a weak recipe match. Simulated interview 5 would trust a substitution they cannot judge. Simulated interview 8 does not want a guessed protein number presented as exact. ChatGPT T05 and T06 kept chicken out in those chats. | Goals and constraints, plus trust calibration. A beginner cannot audit a confident swap. | Hard dietary filters run before ranking. Substitutions are labeled possible, not safe, and say what changes. Nutrition numbers are labeled estimates until a database supplies them. |
| Decision rights | Interview 1 will not let receipt extraction or “I don’t have spinach” permanently change saved inventory. Simulated interview 4: “Just because something was on my receipt doesn't mean it's still mine or even still in the fridge.” Simulated interview 6 does not want inventory reduced unless the user says an item was consumed. ChatGPT T09 refused to set on-hand spinach to the purchased 2 lb. | Meta-coordination / role partitioning. The model may propose. The user signs persistent pantry truth. | AI suggestion → review → explicit confirmation → persistent update. A conversational exclusion hides recipes for the session and asks before deleting a saved item. |
| Substitution | Simulated interview 5: “If the app tells me sour cream works instead of yogurt, I probably won't know enough to question it.” ChatGPT T08 approved sour cream for Greek yogurt without asking which recipe, and one variant mentioned a chicken rice bowl that was not in the prompt. | Contextual reasoning plus a trust-calibration failure. The user, not the model, accepts the swap. | Show confidence (safe / possible / not recommended) and the effect on flavor, texture, or protein. Ask which recipe is in force before approving a swap. |
| Source faithfulness | Simulated interview 8 wants to know whether “40 grams of protein” was calculated or guessed. ChatGPT T12 listed oil and spices as missing when asked. T11 claimed “only what you have” without being asked to list gaps. Simulated interview 6: available ingredients do not make an oven recipe feasible. | Knowledge infrastructure. Availability, equipment, and nutrition must come from structured state, not from fluent generation. | Membership and equipment checks are mandatory. Protein figures in the demo are labeled estimates. A later source should be a nutrition database, with the label calculated or estimated. |

## Speed-dating table

Eight interview slots are required. Interview 1 is the phone note. Interviews 3–9 are the simulated notes. Interview 2 is empty.

| Participant | Accuracy / hallucination | Reliability / consistency | Latency / performance | UX friction | Safety / guardrails | Cost / efficiency | Key finding |
|---|---|---|---|---|---|---|---|
| Interview 1 — graduate student, cooks 3–4×/week, phone. See `validation/interviews/pilot-interview-01.md`. | Will not trust automatic adds from abbreviated receipts or non-food lines. | Spinach marked unavailable must stay out of later recipes. Hard preferences must last the session. | About 5–10 seconds is acceptable for receipt processing. About 30 seconds on every preference change is not. | Wants receipt, text, and voice. Constant manual consumption updates would be too much work. | “I don’t have spinach” may hide recipes now, but must not delete saved spinach without a confirm. | Worth it only if it beats searching Google or YouTube after correction cost. | Do not write pantry truth from extraction or chat alone. |
| Interview 2 | Not supplied. | Not supplied. | Not supplied. | Not supplied. | Not supplied. | Not supplied. | Not supplied. |
| Interview 3 — undergraduate, 20–30 minutes for dinner. Simulated. | Frustrated if a recommendation needs ingredients they do not have. | “Under 20 minutes” is strict. Repeated longer recipes would end trust. | Recommendations within a few seconds. Receipt processing may be slower. | Prefers “rice, eggs, spinach” over entering every quantity and unit. | Comfortable with suggested inventory changes if there is undo or confirmation. | Wants to cook what is at home instead of ordering. | “If I still have to go buy three things, then I could have just looked up a recipe myself.” Rank Cook Now first. |
| Interview 4 — graduate student, shared apartment. Simulated. | A receipt can contain other people's groceries. | Wants shared versus personal ingredients remembered. | Will spend longer on confirmation if later recommendations are then correct. | Someone else may eat an ingredient, so the pantry goes stale. | Do not reduce inventory unless the user says an item was consumed. | Could reduce duplicate purchases in a shared household. | “Just because something was on my receipt doesn't mean it's still mine or even still in the fridge.” |
| Interview 5 — beginner cook. Simulated. | Would trust a substitution they cannot judge. | Steps must match the ingredient list. | A clear answer matters more than speed. | Wants short steps and less cooking jargon. | Label swaps safe, possible, or not recommended. | A swap is useful when buying a whole ingredient for one recipe is wasteful. | “If the app tells me sour cream works instead of yogurt, I probably won't know enough to question it.” |
| Interview 6 — one pan, one pot, microwave, no oven. Simulated. | A recipe that needs missing equipment is not feasible. | Equipment preferences must persist. | Prefers three good recipes rather than a long list. | Does not want to re-enter equipment. | Say when a step assumes equipment that is not on the profile. | Will not buy special equipment for one suggested meal. | “Having all the ingredients doesn't help if the recipe suddenly tells me to put something in an oven.” |
| Interview 7 — vegetarian who sometimes cooks for friends. Simulated. | A dietary violation is more serious than a weak match. | Vegetarian stays on until explicitly changed. | Correctness over speed for diet filtering. | Does not want to retype “vegetarian” every request. | Diet is a hard constraint, not a ranking bonus. | Pantry meals matter because specialty vegetarian products cost more. | “Vegetarian isn't something the ranking algorithm should decide to ignore because another recipe scores higher.” |
| Interview 8 — high-protein, no strict diet. Simulated. | Skeptical of model-written protein numbers. | “High protein” should rerank, not wipe out other recipes. | A short delay is fine if the number comes from reliable data. | Wants a simple filter, not a nutrition essay. | Do not present an estimate as an exact value. | Wants affordable high-protein meals from groceries already owned. | “If it says 40 grams of protein, I want to know whether that's calculated or just something the AI guessed.” |
| Interview 9 — vegetarian, no dairy, spicy, under 30 minutes. Simulated. | Biggest fear is the model dropping one constraint from a stack. | Dietary restrictions persist across conversational edits. | Will answer one clarification if constraints conflict. | Retyping six preferences every time is tiring. | Ask a focused question instead of guessing. | Specialized ingredients raise cost, so pantry fit still matters. | “I'd rather it ask me one question than confidently recommend something I specifically said I can't eat.” |

## Synthesis

Repeated across the notes:

1. Pantry feasibility beats variety. Cook Now comes before a shopping list.
2. A receipt is purchase evidence, not current or personal inventory.
3. Diet is a hard constraint. High protein is a soft preference.
4. Beginners will over-trust a confident substitution.
5. Equipment belongs in the feasibility check.
6. Nutrition numbers need a source label.
7. Persistent profile state should make people stop repeating themselves, and a conflict should produce one question rather than a confident violation.
8. Inventory upkeep fails if it is more work than searching for a recipe.

ChatGPT did not fail every one of these. T01, T03, T06, T09, and T12 were conservative about quantities, missing chicken, purchase versus on-hand, and listed gaps. The partials that match the interviews are T02 (ambiguous parse), T08 (unguarded substitution and stray context), T10 (time claim without asking), and T11 (staples treated as owned). A second platform is not in the repo yet, so these are not cross-platform findings.
