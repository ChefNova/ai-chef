# ChefNova — Checkpoint 2 Submission Package

This directory is the **CP2 submission layer** for the existing ChefNova repository. It contains the validation protocol, theoretical lens, evidence-to-design framework, refined design specification, prototype, presentation structure, and project-management artifacts required by Checkpoint 2.

## Submission status

The evidence chain is filled from the ChatGPT transcript, one phone interview, and seven notes that were supplied as **simulated** interviews. Those simulated notes are labeled as simulated in `validation/interviews/simulated-interviews-03-09.md`. They are not presented as live speed-dating transcripts.

Still open before this is a complete Checkpoint 2 package:

1. A second AI platform. `validation/transcripts/gemini_outputs.md` is still empty. ChatGPT is in `validation/transcripts/chatgpt_outputs.md`.
2. Interview 2. It was not supplied.
3. Each member's own reflection and the class storyboard in `validation/reflections/`.
4. Screenshot files named in the ChatGPT log are not in the repo. The transcript is the receipt.
5. Slides still need to be posted to Canvas. The outline is in `presentation/CP2_SLIDE_OUTLINE.md`.

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
