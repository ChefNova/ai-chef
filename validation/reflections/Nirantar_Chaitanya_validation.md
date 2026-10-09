# CP2 Individual Reflection — Chaitanya Nirantar

## Role

Prompting Study & Protocol

---

## Prompting study notes

### Platforms tested

- **ChatGPT (GPT-4o)** — primary platform, 7–8 Oct 2026
- **Gemini 1.5 Pro** — secondary platform (outputs in `validation/transcripts/gemini_outputs.md`)

### Scenarios run

All twelve scenarios from `validation/PROMPTING_PROTOCOL.md` were run on ChatGPT. Gemini was run on a focused subset (T01, T04, T05, T09, T10) for cross-platform comparison.

| Scenario | Type | Pillar | ChatGPT result | Gemini result |
|---|---|---|---|---|
| T01 — Typical receipt extraction | typical | reasoning | Pass — did not invent quantities | Pass — similar conservative output |
| T02 — Abbreviated receipt | edge | reasoning | Partial — merged "whole" and "2%", promoted a likely count | Partial — resolved ambiguity without flagging it |
| T03 — Unknown package size | edge | reasoning | Pass — asked for confirmation | Pass |
| T04 — Multi-turn dietary constraint | typical | memory | Pass — retained vegetarian + protein + time across turns | Pass — retained constraints |
| T05 — Explicit exclusion (no chicken) | failure | memory | Pass — kept chicken out; may have used account memory | Pass |
| T06 — Missing core ingredient | failure | reasoning | Pass — flagged chicken as missing | Not tested |
| T07 — Optional ingredient (no lemon) | edge | reasoning | Pass — correctly called lemon optional | Not tested |
| T08 — Substitution (sour cream for yogurt) | edge | reasoning | **Partial** — approved swap without asking which recipe; invented a chicken rice bowl context | Not tested |
| T09 — Inventory decision rights | failure | meta-coordination | Pass — stated that purchased 2 lb ≠ on-hand stock | **Partial** — Gemini said it would update inventory automatically unless told otherwise |
| T10 — Constraint overload | edge | attention | **Partial** — retained salient constraints; claimed ~15 min while assuming cooked rice | **Partial** — dropped "no mushrooms" from the output |
| T11 — Stale inventory | failure | memory | **Partial** — removed spinach from recommendations but still required oil as if owned | Not tested |
| T12 — Source faithfulness | edge | reasoning | Pass — listed missing ingredients explicitly | Not tested |

### Key failure screenshots

- **T08:** ChatGPT approved sour cream for Greek yogurt and introduced a chicken rice bowl that was not in the prompt. This is a reasoning failure — the model closed an ambiguous context by inventing one.
- **T09 (Gemini):** Gemini said it would update inventory automatically from a receipt unless told otherwise. This is a meta-coordination failure — the AI assumed it owned pantry truth.
- **T10 (Gemini):** Under the eight-constraint prompt, Gemini dropped "no mushrooms" and produced a recipe with mushrooms. This is an attention failure — a quieter constraint in a dense stack was lost.
- **T11:** ChatGPT removed spinach from active recommendations but still listed oil as an available ingredient in the same response. Conversational memory and structured inventory are not the same thing.

---

## Speed-dating interviews

### Interview 3 — Undergraduate student, time-constrained cook

- **Participant:** Undergraduate student living off campus, cooks 2–3 times a week, usually has 20–30 minutes for dinner.
- **Task shown:** Early ChefNova flow — receipt upload, pantry confirmation, recipe recommendation screen.
- **Main finding:** Pantry feasibility matters more than recipe variety. If the top recommendation still requires a grocery run, the app has not saved any effort.
- **Quote:** "If I still have to go buy three things, then I could have just looked up a recipe myself."
- **Complementarity interpretation:** The hybrid fails at the core task if the AI generates plausible recipes rather than feasible ones. Complementarity requires the AI to filter against confirmed pantry state — not to produce a long ranked list and let the user check what is missing.
- **Design implication:** Cook Now recipes ranked first. A recipe labeled Cook Now must pass a structured feasibility check against confirmed inventory, not a language-model estimate.

### Interview 8 — Graduate student, gym-focused, high-protein goal

- **Participant:** Graduate student who trains regularly and tracks protein intake but has no strict dietary restrictions.
- **Task shown:** Nutrition display mock-up showing a ChefNova match score and an estimated protein value.
- **Main finding:** A protein number without a source label is not useful. The participant said they would treat an unexplained number as an AI guess and ignore it.
- **Quote:** "If it says 40 grams of protein, I want to know whether that's calculated or just something the AI guessed."
- **Complementarity interpretation:** This is a knowledge-infrastructure failure. The AI can generate a fluent number, but fluency does not equal accuracy. The human cannot supply the missing verification — they have no way to check the claim without a source. Trust calibration breaks because confidence is decoupled from evidence.
- **Design implication:** Nutrition values must be labeled. Demo figures carry an "estimate" label. A production version would pull from a nutrition database and label values calculated versus estimated. The model must not present a generated number as a measurement.

---

## Finding that changed my assumption

**Initial assumption:** I expected the main failure mode from the prompting study to be hallucination — the model inventing ingredients or recipes that do not exist.

**What I actually found:** The more pervasive problem is *quiet constraint dropping* under load, not invention. T10 showed that ChatGPT retained the most prominent constraint ("vegetarian," "under 20 minutes") but silently assumed cooked rice to satisfy the time limit — a constraint violation by assumption rather than by omission. Gemini dropped "no mushrooms" entirely from an eight-constraint prompt.

Interview 8 sharpened this further in a different direction: the problem is not only what the model forgets but also what it generates with false confidence. The participant could not detect a guessed protein number. A fluent, specific answer produces stronger overtrust than a vague one — and beginners have no way to audit it.

**Theoretical connection — attention orchestration and trust calibration:**

Gonzalez et al. describe attention orchestration as the design of the interface to surface what requires human judgment. Both failures above are attention failures. In T10, the model did not surface the tension between "under 20 minutes" and "cooked rice" — it resolved it silently. In Interview 8, the interface did not surface whether the protein value came from a database or was generated — it presented both the same way.

The complementarity claim for ChefNova is that the AI owns candidate generation and reasoning while the human owns acceptance and verification. That partition only holds if the AI surfaces the moments where it is uncertain or where it resolved an ambiguity on its own. An interface that hides those moments shifts the verification burden onto the user without giving them the signal they need to exercise it.

---

## How this affected the design

Two specific changes in `DESIGN_SPEC.md` trace directly to these findings:

1. **Hard constraint enforcement in application logic, not in the prompt.** Dietary restrictions, time limits, and explicit exclusions are enforced by the application layer before the ranked list is produced. The LLM does not decide whether a constraint is met. This addresses both the T10 finding (quiet constraint drop) and Interview 7's concern about a score overriding a dietary hard filter.

2. **Source labeling on all generated numbers.** Any nutrition value shown in the UI carries one of three labels: *calculated* (from a nutrition API), *estimated* (model-generated from recipe context), or *unavailable*. This directly addresses Interview 8 and the T08 finding. The design does not suppress the number — it exposes its provenance so the human can calibrate trust appropriately.

Both changes implement the role-partitioning principle from Gonzalez et al.: constraint checking is application logic (deterministic, auditable), not language-model reasoning (fluent, silent about uncertainty).

---

## Class storyboard

<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/3d928d19-8d28-49a0-aad0-009530ca7890" />

