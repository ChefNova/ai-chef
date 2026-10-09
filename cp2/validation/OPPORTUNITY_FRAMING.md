# ChefNova CP2 Opportunity Framing

## Purpose

Translate CP2 evidence and the complementarity lens into prioritized product requirements.

Evidence below is the ChatGPT transcript, phone interview 1, and speed-dating interviews 3–9. Interview 2 was not supplied. This is not a ranking from eight live speed-dating sessions, and it is not a second AI platform.

## Hypothesis evolution

| Initial assumption | CP2 evidence | Updated understanding | Resulting design change |
|---|---|---|---|
| Receipt extraction is a major source of ambiguity. | ChatGPT T01 did not invent quantities. T02 merged “whole” and “2%” and promoted a likely count. Interview 1 and interview 4 also refuse automatic saves from a receipt. | The failure to design for is an unresolved parse and mixed ownership, not wholesale invention. | Keep raw text, flag conflicts, and confirm before save. |
| Users should remain the source of truth for current inventory. | T09, interview 1, and interview 4 all separate purchase from on-hand or personal stock. | Confirmed. A receipt is not the pantry. | User-confirmed inventory stays authoritative. |
| We thought variety and discovery were the main value. | Interview 3: “If I still have to go buy three things, then I could have just looked up a recipe myself.” | Feasibility beats variety for time-constrained cooks. | Rank Cook Now before recipes that need shopping. |
| Recipe feasibility is ingredient-name matching. | Interview 6 (oven). ChatGPT T11 (oil treated as owned). Interview 1 distinguishes a missing lemon from missing chicken. | Feasibility includes core versus optional ingredients, staples, and equipment. | Required / optional / substitutable roles, plus a kitchen profile. |
| Dietary and protein goals are similar preferences. | Interview 7 says vegetarian must not be outranked. Interview 8 says high protein should influence order, not erase other recipes. | Diet is a hard constraint. Protein is a soft preference. | Filter diet before scoring. Protein only changes rank. |
| Conversational memory is enough to hold constraints. | T04 and T05 retained constraints in one chat, and T05 may have used account memory. Interview 9 is afraid one constraint in a stack will be dropped. | The application, not the chat transcript, has to hold the profile. | Structured persistent constraints, plus one clarification when they conflict. |
| A confident substitution is helpful. | Interview 5 would not know enough to question sour cream for yogurt. T08 approved it without the recipe. | Beginners over-trust fluent advice. That is a complementarity break, not a feature request. | Show confidence and the effect on flavor, texture, or protein. |
| Generated nutrition can be shown as a fact. | Interview 8 asks whether 40 g was calculated or guessed. | A number without a source is a knowledge-infrastructure failure. | Label estimates. Do not present a model guess as a measurement. |

## Prioritized requirements

Each row uses the form: evidence shows a complementarity break; a Gonzalez design principle addresses it.

| Priority | Requirement | Evidence | Theory | Design response |
|---|---|---|---|---|
| P0 | User-confirmed inventory | Interview 1 and interview 4 show the break where the model would own pantry truth. T09 shows the model can state the right rule and still must not be the writer of record. | Role partitioning / meta-coordination | AI suggestion → review → explicit confirmation → persistent update |
| P0 | Hard-constraint preservation | Interviews 7 and 9 show a ranking score or a long prompt must not relax diet. T10 shows a time claim that skipped prep state. | Goals and constraints / memory | Persist diet, exclusions, and max time. Enforce them in code before ranking. |
| P0 | Cook Now feasibility, including equipment and staples | Interview 3 shows variety without pantry fit is not complementary. Interview 6 shows ingredients without the oven are not feasible. T11 shows unlisted oil. | Knowledge infrastructure / role partitioning | Order Cook Now, then Almost Ready, then Needs Shopping. Check equipment. Do not treat staples as owned unless they are in inventory. |
| P1 | Substitution confidence | Interview 5 and T08 show over-trust and missing recipe context. | Trust calibration / interrogation | Label safe, possible, or not recommended. Say what changes. Ask before a permanent acceptance. |
| P1 | Clarification on conflict | Interview 9 and T10 show a confident answer when a question was required. | Attention and interrogation orchestration | Ask one focused question. Do not ask when structured state is already enough. |
| P1 | Explain the recommendation | Interview 1 trusts a recipe more when the reason is visible, and does not trust a bare match score. | Shared mental model | Show “Why this?” and the factors behind a score: pantry, diet, time, protein. |
| P1 | Nutrition provenance | Interview 8 shows an unlabeled protein number is not usable. | Knowledge infrastructure | Demo figures say “estimate.” A later version uses a nutrition source and labels calculated versus estimated. |
| P2 | Lightweight inventory edits | Interview 1 and interview 3 show upkeep can erase the time saved. | Attention orchestration | Receipt, typed lists, voice, and quick edits. Confirmation stays short. |
| P2 | Saved kitchen and preference profile | Interviews 6 and 9 show repeated entry of equipment and diet. | Memory / shared mental model | Equipment and hard preferences persist until the user changes them. |

## Scope boundaries

- Automatic consumption tracking is outside the initial scope. Interview 4 supports that: do not reduce stock unless the user says an item was used.
- Purchased quantities are never assumed to equal current inventory.
- Grocery ordering APIs are outside the initial scope.
- ChefNova does not make medical or allergy-grade safety claims.
- Nutrition values are not presented as model-measured facts.
- Shared-versus-personal ownership (interview 4) is recorded as a requirement to confirm what is yours. A full household account model is not in this prototype.
