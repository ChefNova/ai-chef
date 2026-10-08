# Speed-Dating Interview 02

## Metadata

- **Interview type:** Speed-dating (real user, not simulated)
- **Date:** October 2026
- **Duration:** ~8 minutes
- **Interviewer:** Ananya Jandhyala
- **Participant profile:** Experienced home cook; plans meals for a multi-person household (family with varying dietary restrictions); uses a mix of pantry-first and recipe-first strategies depending on the day
- **Consent:** Verbal consent obtained; name withheld from record

---

## Context

The participant was shown a prototype walkthrough of ChefNova and asked to react to two core flows: **Cook Now** (pantry-first: what can I make tonight?) and **Plan a Meal** (recipe-first: I want to make X, what do I need?). The session focused on how the participant currently manages household constraints, how they decide what to cook, and where they felt the AI would or would not fit their workflow.

---

## Key Findings

### 1. Four-Level Constraint Model

The participant described household dietary constraints as falling into four distinct priority tiers, which they enforced with different levels of flexibility:

| Level | Type | Example | Negotiability |
|-------|------|---------|---------------|
| 1 | Allergy | Peanut allergy (family member) | Non-negotiable. Hard block. |
| 2 | Dietary restriction | Vegetarian (family member) | Hard filter. No exceptions. |
| 3 | Dislike | "My kid won't eat mushrooms" | Soft. Can be overridden for special meals. |
| 4 | Preference | Prefers spicy food | Ranking signal only. |

> "Peanuts aren't a preference — that's a safety thing. The app can't treat that the same as 'I'd rather not have mushrooms tonight.'"

**Gap identified:** Current AI tools (as tested in T04/T05) treat all constraints as a single ranking signal. A flattened hierarchy is a safety failure for allergy-level constraints. See **Gap 03 — Constraint Hierarchy Flattened** in GAP_ANALYSIS.md.

---

### 2. Household Profiles, Not Individual Preferences

The participant plans for multiple people with different restrictions simultaneously. They do not think of the meal as satisfying *their* preferences — they think of it as satisfying the household's constraint matrix.

> "I'm not cooking for myself. I have to think about what works for everyone at the table."

The ChefNova prototype showed a single-user preference model. The participant immediately asked: "Can I set up different profiles for each person?"

**Design implication:** ChefNova should support household profiles where each member carries their own constraint tiers. The recommendation engine should filter against the union of all active hard constraints (allergy + dietary restriction) across all household members.

---

### 3. Dual Entry Points: Cook Now vs. Plan a Meal

The participant was the clearest of any interviewee in articulating two fundamentally different starting points:

- **Cook Now:** "I open the fridge, I see what I have, I want something I can make in the next 30 minutes without going to the store." → Pantry-first. Minimize shopping. Maximize use of what's available.
- **Plan a Meal:** "I already know I want to make biryani on Saturday. I need to know what to buy." → Recipe-first. Meal is fixed; shopping list is the output.

> "If I'm in Plan a Meal mode, I don't care what's in my pantry right now. I care about what I need to buy. Those are completely different problems."

**Gap identified:** A single pantry-first interface forces the wrong starting point for recipe-first planners. The app must not decide the user's optimization objective for them. See **Gap 06 — Pantry-First ≠ Goal-Driven Planning** in GAP_ANALYSIS.md.

---

### 4. Experienced Cook's Skepticism of AI Ingredient Matching

The participant expressed that for experienced cooks, the value of an AI meal planner is not in suggesting *what* to cook — they already know. The value is in logistics: tracking what's available, flagging what's missing, and building a shopping list.

> "I know how to cook. What I don't want to do is stand in front of the fridge trying to remember if I used the last of the cumin."

This shifts the AI's role from *recommender* to *inventory assistant* and *constraint enforcer* for this user segment. The AI should trust the experienced cook's culinary judgment and focus on the operational layer.

---

### 5. Trust Threshold for Autonomous Inventory Updates

When shown the T09 scenario (receipt scan → auto-set inventory), the participant's reaction was immediate refusal.

> "No. Just because I bought it doesn't mean I have it. I might have given half to my neighbor."

The participant wanted to *review and confirm* any AI-proposed inventory update before it was applied. They distinguished between:

- **Purchase evidence** (what the receipt shows I bought)
- **Current stock** (what I actually have right now)

This corroborates the T09 finding and the Gap 01 (Inventory Decision Rights) design implication.

---

## Summary of Gaps Surfaced

| Gap | Label | Source |
|-----|-------|--------|
| 01 | Inventory Decision Rights | T09 + this interview |
| 03 | Constraint Hierarchy Flattened | This interview (primary source) |
| 06 | Pantry-First ≠ Goal-Driven Planning | This interview (primary source) |

---

## Raw Notes

- Participant immediately understood both Cook Now and Plan a Meal as distinct modes — did not need explanation.
- Asked about household profiles unprompted within first 2 minutes.
- Strong reaction to peanut allergy being treated as a preference: "That's a liability, not a feature."
- Comfortable with AI as inventory tracker; skeptical of AI as meal recommender for experienced cooks.
- Said she would use Plan a Meal weekly (Saturday meal prep) and Cook Now 2–3 times per week for weeknights.
- Suggested the app show a "confidence" score on time estimates: "If it says 20 minutes, does that assume the rice is already cooked?"
