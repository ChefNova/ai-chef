# ChefNova CP2 Gap Analysis

## Purpose

This matrix connects CP2 evidence to the human–AI teaming lens and then to concrete ChefNova design decisions. The required reasoning chain is:

**Receipt → Theory → Design**

The theoretical interpretation is based on Gonzalez et al. (2026), *Toward a science of human–AI teaming for decision making: A complementarity framework*.

## Cross-cutting gap matrix

The design hypotheses below are deliberately specified before evidence collection. The empirical column is the only portion that must be populated from the team's actual AI receipts and speed-dating interviews.

| Dimension | Empirical receipt to attach | Theoretical reading | ChefNova design response |
|---|---|---|---|
| Accuracy | Receipt parsing result showing correct/incorrect item or quantity interpretation | Reasoning / knowledge-infrastructure gap | Preserve original receipt text, expose uncertainty, and require confirmation for ambiguous fields |
| Reliability | Repeated runs of the same meal request | Shared mental-model / role-ambiguity risk | Keep structured inventory as source of truth and apply deterministic feasibility checks |
| Memory | Multi-turn request where dietary/time constraints are added or revised | Memory / shared-state failure | Persist active constraints separately from raw conversation text |
| UX friction | User response to repeated questions or long prompts | Attention / interrogation orchestration | Surface only conflicts and ask focused clarification questions |
| Safety | Explicit dietary exclusion or hard constraint | Goals-and-constraints / role-partition failure | Never silently relax hard constraints; escalate uncertainty |
| Decision rights | Interview 1 (phone, graduate student who cooks 3–4 times a week): would not let receipt extraction or “I don’t have spinach” permanently change saved inventory without confirmation. Full notes: `validation/interviews/pilot-interview-01.md` | Meta-coordination / role partitioning: AI proposes; the user confirms persistent pantry truth | AI suggestion → review → explicit confirmation → persistent inventory update |
| Substitution | Model treatment of a missing ingredient | Contextual reasoning / decision-rights issue | Classify ingredient role and let the user accept/reject uncertain substitutions |
| Source faithfulness | Availability or recipe explanation compared with structured inventory/source | Knowledge-infrastructure issue | Ground factual availability claims in structured state and retrieved sources |

## Speed-dating evidence structure

Eight interviews are required: two per team member. The completed notes should use the same six dimensions so results can be compared across participants.

| Participant | Accuracy / hallucination | Reliability / consistency | Latency / performance | UX friction | Safety / guardrails | Cost / efficiency | Key finding |
|---|---|---|---|---|---|---|---|
| Interview 1 — graduate student, cooks 3–4×/week, phone. Interviewer not named. See `validation/interviews/pilot-interview-01.md`. | Will not trust automatic adds from abbreviated receipts or non-food lines. Wants review before confirm. | Spinach marked unavailable must stay out of later recipes. Vegetarian and other hard preferences must last the session. | About 5–10 seconds is acceptable for receipt processing. About 30 seconds on every preference change is not. | Wants receipt, text, and voice. Updating every consumed item by hand could cost more effort than searching for a recipe. | “I don’t have spinach” may hide recipes for this session, but must not delete saved spinach without a confirm. | Worth it only if it saves time versus Google or YouTube after the cost of corrections. | Do not write pantry truth from extraction or chat alone. |
| Interview 2 | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Insert actual finding |
| Interview 3 | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Insert actual finding |
| Interview 4 | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Insert actual finding |
| Interview 5 | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Insert actual finding |
| Interview 6 | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Insert actual finding |
| Interview 7 | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Insert actual finding |
| Interview 8 | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Evidence receipt | Insert actual finding |

## Synthesis criteria

After evidence collection, the final synthesis should identify:

1. Repeated failures across AI platforms.
2. Repeated user pain points.
3. Safety- or constraint-critical failures.
4. Problems better addressed through interface/state than model capability.
5. Problems that require prompting, retrieval, or model improvement.

A design change is carried forward when the evidence supports a concrete requirement and the failure has a defensible theoretical interpretation.
