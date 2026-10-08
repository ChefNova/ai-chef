# ChefNova CP2 Theory Lens

## Required theoretical lens

Gonzalez et al. (2026), *Toward a science of human–AI teaming for decision making: A complementarity framework.*

## Working theory claim

> **ChefNova's hybrid should outperform human-alone and AI-alone at feasible meal selection because the AI can handle language interpretation, candidate generation, and conversational reasoning while the human retains final decision rights over actual inventory, dietary constraints, and ambiguous evidence.**

This is a working hypothesis to be tested in CP2/CP3, not a demonstrated result.

## Complementarity model for ChefNova

### Human ownership

**Reasoning**
- Decide whether the extracted inventory reflects reality.
- Decide whether a substitution is acceptable.
- Decide whether an ambiguous ingredient should be included.
- Make final food/dietary choices.

**Memory**
- Confirm what is actually still available.
- Correct stale or incorrect quantities.
- Provide personal preferences that should remain authoritative.

**Attention**
- Focus on exceptions, uncertainty, and decisions that require confirmation.
- Avoid manually checking every recipe ingredient when the system can surface only the conflicts.

### AI ownership

**Reasoning**
- Interpret messy receipt language.
- Interpret flexible natural-language meal requests.
- Generate and explain candidate meals.
- Identify possible substitutions and their uncertainty.

**Memory support**
- Maintain structured conversational constraints.
- Retrieve confirmed inventory state.
- Carry active requirements across turns.

**Attention support**
- Surface missing core ingredients.
- Highlight uncertain quantities.
- Ask focused clarification questions rather than forcing a long form.

### Meta-coordination

The user owns final inventory truth. The AI must escalate when evidence is insufficient, when a hard constraint conflicts with a candidate, or when a substitution is uncertain.

## Evidence → theory → design

Sources: ChatGPT transcript; phone interview 1; simulated interviews 3–9. Interview 2 was not supplied. Gemini was not run.

| Evidence receipt | Theoretical interpretation | Design implication |
|---|---|---|
| Interview 1 and simulated interview 4 refuse to treat a receipt, or “I don’t have spinach,” as a saved-pantry write. ChatGPT T09 said a purchased 2 lb is not on-hand stock. | Meta-coordination. Complementarity holds only if the model proposes a parse and the human signs persistent inventory. | AI suggestion → review → explicit confirmation → persistent update. Session exclusions do not delete saved items. |
| Simulated interview 3: a recipe that still needs three purchases is not worth the app. ChatGPT T11 said “using only what you have” while requiring oil. | Knowledge infrastructure. Feasibility is a state check, not a fluent claim. | Rank Cook Now ahead of Needs Shopping. Include staples and equipment in the check. |
| Simulated interview 5 would accept “sour cream works instead of yogurt” without being able to judge it. ChatGPT T08 approved that swap and one variant invented a chicken rice bowl. | Trust calibration and role partitioning. A beginner cannot supply the missing judgment, so the model must expose uncertainty instead of sounding final. | Label a swap safe, possible, or not recommended, and say what changes. Ask which recipe is in force. |
| Simulated interview 7: vegetarian must not lose to a higher score. Simulated interview 9 would rather be asked one question than be served a forbidden meal. ChatGPT T10 kept the salient exclusions and still assumed cooked rice to hit the time claim. | Goals and constraints, plus attention orchestration. Salient words can be retained while a quieter constraint is skipped. | Hard-filter diet, time, and exclusions in code. Keep them in a profile so they are not retyped. Ask when the set conflicts. |
| Simulated interview 6: an oven step makes a fully stocked recipe infeasible. Simulated interview 8: “40 grams of protein” must say whether it was calculated or guessed. | The same knowledge-infrastructure rule covers tools and numbers. If it is not in structured state or a cited source, it is not a fact. | Save a kitchen profile and block or label missing equipment. Label demo protein figures as estimates until a nutrition source is attached. |

## Design principle

### Role partitioning

ChefNova will partition responsibilities instead of asking the LLM to control the whole workflow.

**User controls:**
- confirmed inventory
- hard dietary restrictions
- acceptance/rejection of substitutions
- final recipe choice

**Application logic controls:**
- quantity comparison
- unit compatibility
- inventory persistence
- hard-rule enforcement

**GenAI controls:**
- natural-language interpretation
- candidate generation
- contextual explanation
- conversational refinement

## CP3 evaluation

The complementarity claim should ultimately be compared against:
1. Human-alone baseline
2. AI-alone baseline
3. ChefNova hybrid

The goal is not to prove that the AI is universally better. The test is whether the division of labor produces better task outcomes on the selected meal-planning tasks.
