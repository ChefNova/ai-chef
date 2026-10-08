# ChefNova — Checkpoint 2 Submission Package

This directory is the **CP2 submission layer** for the existing ChefNova repository. It contains the validation protocol, theoretical lens, evidence-to-design framework, refined design specification, prototype, presentation structure, and project-management artifacts required by Checkpoint 2.

## Submission status

The package is **submission-ready except for evidence that can only come from real-world execution**. No AI-platform output or interview finding is fabricated here.

The only evidence-dependent inputs are:

1. **Prompting receipts:** actual outputs/screenshots from at least two AI platforms using the controlled scenarios in `validation/PROMPTING_PROTOCOL.md`.
2. **Speed-dating receipts:** two interviews per team member (eight total), recorded in `validation/GAP_ANALYSIS.md` and individual validation reflections.
3. **Evidence-linked revisions:** once those receipts exist, the evidence columns/rows in `GAP_ANALYSIS.md`, `THEORY_LENS.md`, and `OPPORTUNITY_FRAMING.md` are populated with the observed results. The surrounding analysis, theory structure, requirements, design, prototype, and presentation structure are already prepared.

These are empirical inputs, not missing project design work.

## CP2 structure

- `validation/PROMPTING_PROTOCOL.md` — finalized controlled prompting study protocol
- `validation/transcripts/` — evidence location for actual AI receipts
- `validation/GAP_ANALYSIS.md` — finalized evidence → theory → design framework
- `validation/THEORY_LENS.md` — Gonzalez et al. complementarity analysis
- `validation/OPPORTUNITY_FRAMING.md` — prioritized ChefNova requirements and hypothesis-evolution framework
- `validation/reflections/` — individual CP2 reflection documents
- `DESIGN_SPEC.md` — refined ChefNova interaction and design specification
- `prototype/` — functional Streamlit proof-of-concept
- `presentation/CP2_SLIDE_OUTLINE.md` — final 7-slide presentation structure
- `project-management/CP2_ISSUES.md` — CP2 GitHub issue definitions and ownership map

## CP2 design thesis

> **ChefNova uses AI for interpretation and conversational reasoning while the user retains final decision rights over inventory, hard constraints, substitutions, and recipe choice.**

The CP2 workflow follows the required chain:

**Receipt → Theory → Design**

The prototype and design specification operationalize that division of labor through receipt extraction, user-confirmed inventory, structured constraints, deterministic feasibility checks, clarification, and conversational refinement.

## Existing CP1 repository

This package is intended to be merged into the existing ChefNova CP1 repository without replacing the team's literature, proposal, or existing reflections.
