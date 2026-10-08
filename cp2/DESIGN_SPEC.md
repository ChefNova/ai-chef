# ChefNova — Checkpoint 2 Design Specification

## 1. Product goal

Help college students and beginner home cooks move from messy grocery information to a meal they can realistically prepare.

## 2. Core design principle

> **The AI interprets and recommends; the user owns the truth about what is actually available.**

This preserves human decision rights while allowing GenAI to handle ambiguity and conversational requests.

## 3. Primary persona

### College student / beginner home cook

Needs:
- quick meal decisions
- low planning effort
- simple ingredient explanations
- dietary/preference support
- confidence that the recipe is actually feasible

Mental model:
> “I don't want to search ten recipes and then discover I am missing half the ingredients.”

## 4. Decision rights

| Decision | Owner |
|---|---|
| What was purchased? | Receipt evidence / AI extraction |
| What remains? | **User** |
| Is a quantity uncertain? | AI flags; **user confirms** |
| Is a hard dietary restriction active? | **User** |
| Is a substitution acceptable? | AI proposes; **user decides** |
| Does a recipe meet inventory requirements? | Application logic checks; AI explains |
| Which recipe to cook? | **User** |

## 5. End-to-end journey

```text
Receipt / order screenshot
        ↓
Multimodal extraction
        ↓
Candidate grocery items + quantities
        ↓
User review / correction
        ↓
Confirmed inventory
        ↓
Natural-language meal request
        ↓
Constraint extraction
        ↓
Recipe candidates
        ↓
Deterministic inventory + hard-constraint checks
        ↓
Feasible candidates
        ↓
AI explanation / adaptation
        ↓
User selects or refines
```

## 6. Receipt workflow

### Step A — Upload

User uploads a grocery receipt or online grocery order screenshot.

### Step B — Extraction

AI proposes:
- normalized item name
- quantity
- unit
- uncertainty

Original receipt text remains available for verification.

### Step C — Confirmation

User edits incorrect values.

The system does not treat the receipt as proof of current inventory.

## 7. Meal request workflow

Example:

> “I want something vegetarian, high protein, and under 20 minutes.”

The system extracts structured constraints:
- diet = vegetarian
- protein preference = high
- max time = 20 minutes

It should preserve these constraints across refinement.

## 8. Recommendation behavior

The system should:
1. Generate/retrieve candidates.
2. Check confirmed inventory.
3. Reject or flag candidates with missing required ingredients.
4. Allow reasonable substitutions.
5. Keep optional/flavoring ingredients from unnecessarily eliminating a recipe.
6. Surface uncertainty.
7. Explain what is available, missing, or substituted.

## 9. Ingredient roles

Ingredient importance is recipe-specific.

- **Required:** recipe cannot reasonably proceed without it.
- **Optional:** omission is acceptable.
- **Substitutable:** reasonable alternative exists.
- **Flavoring:** useful but not central.
- **Staple:** common assumed ingredient, but should be made visible if needed.

The system must not assign a universal role to an ingredient independent of recipe context.

## 10. Interrogation moments

Ask the user when:
- receipt quantity is ambiguous
- package size is unknown
- a hard constraint conflicts with all feasible candidates
- a substitution has meaningful uncertainty
- inventory is stale or contradictory

Avoid asking when the system can safely proceed using confirmed structured data.

## 11. Trust calibration

Show:
- “Confirmed by you”
- “Extracted from receipt”
- “Uncertain — please confirm”
- “Missing from confirmed inventory”
- “Suggested substitution”
- recipe source/provenance

Do not present model inference as inventory fact.

## 12. Technical responsibility split

### GenAI
- receipt language interpretation
- conversational constraint interpretation
- recipe reasoning
- substitution explanation
- conversational refinement

### Application logic
- persistence
- inventory state
- quantity comparison
- compatible-unit validation
- hard-rule enforcement

### User
- final inventory confirmation
- hard dietary choices
- substitution acceptance
- final recipe selection

## 13. CP2 evidence traceability

The design decisions below are the pre-registered traceability targets for CP2. Final evidence references are inserted from the actual prompting/interview receipts; the design itself is fully specified.

| Design choice | CP2 evidence | Theory |
|---|---|---|
| User confirms inventory | Prompting/interview evidence on stale purchase information and decision rights | Role partitioning / meta-coordination |
| Persistent constraints | Prompting/interview evidence on multi-turn constraint retention | Memory / shared mental model |
| Clarification for ambiguity | Prompting/interview evidence on ambiguous receipt data | Attention / interrogation orchestration |
| Deterministic quantity checks | Prompting/interview evidence on quantity feasibility | Knowledge infrastructure / role partitioning |

## 14. Prototype acceptance criteria

The prototype must demonstrate:
- receipt upload or simulated receipt input
- editable inventory
- confirmation state
- conversational meal request
- visible constraints
- recipe candidates
- feasibility/missing-item explanation
- user refinement
- clear human decision rights
