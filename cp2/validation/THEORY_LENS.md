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

| Evidence receipt | Theoretical interpretation | Design implication |
|---|---|---|
| PENDING | PENDING | PENDING |
| PENDING | PENDING | PENDING |
| PENDING | PENDING | PENDING |

Replace these rows with at least three observed failures from the prompting study/interviews.

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
