# ChefNova CP2 Opportunity Framing

## Purpose

Translate CP2 evidence and the complementarity lens into prioritized product requirements.

## Hypothesis evolution

The following are the assumptions established from CP1 and the proposed ChefNova design. CP2 evidence determines which assumptions are confirmed, weakened, or rejected.

| Initial assumption | CP2 evidence | Updated understanding | Resulting design change |
|---|---|---|---|
| Receipt extraction is a major source of ambiguity. | Insert actual prompting/interview receipt | Confirm / revise based on evidence | Keep multimodal extraction plus user correction where justified |
| Users should remain the source of truth for current inventory. | Insert actual prompting/interview receipt | Confirm / revise based on evidence | Preserve user-confirmed inventory as authoritative |
| Recipe feasibility depends on more than ingredient-name matching. | Insert actual prompting/interview receipt | Confirm / revise based on evidence | Distinguish required, optional, flavoring, staple, and substitutable ingredients in context |
| Conversational constraints need explicit state. | Insert actual prompting/interview receipt | Confirm / revise based on evidence | Persist active constraints across turns |

## Prioritized requirements

The ordering below is the current design hypothesis derived from the ChefNova concept and CP1. CP2 evidence should confirm or reorder it; it should not be presented as an empirical ranking until the receipts are attached.

| Priority | Requirement | Evidence | Theory | Design response |
|---|---|---|---|---|
| P0 | User-confirmed inventory | Insert actual receipt | Role partitioning / meta-coordination | User reviews extracted items and quantities |
| P0 | Hard-constraint preservation | Insert actual receipt | Goals & constraints / memory | Persist hard constraints and block silent relaxation |
| P0 | Deterministic inventory checks | Insert actual receipt | Knowledge infrastructure / role partitioning | Compare compatible quantities in application logic |
| P1 | Uncertainty + clarification | Insert actual receipt | Attention / interrogation orchestration | Ask only when evidence is insufficient |
| P1 | Ingredient-role reasoning | Insert actual receipt | Reasoning complementarity | Treat ingredient importance as recipe-specific |
| P1 | Missing-item explanation | Insert actual receipt | Shared mental model | Show required missing ingredients and available substitutions |
| P2 | Conversational refinement | Insert actual receipt | Attention orchestration | Let users revise time, diet, protein, cuisine, and other constraints |
| P2 | Recipe-source provenance | Insert actual receipt | Knowledge infrastructure | Surface recipe/source information used for recommendations |

## Scope boundaries

- Automatic consumption tracking is outside the initial scope.
- Purchased quantities are never assumed to equal current inventory.
- Grocery ordering APIs are outside the initial scope.
- ChefNova does not make medical/allergy-grade safety claims.
- Nutrition values are not presented as model-measured facts.
