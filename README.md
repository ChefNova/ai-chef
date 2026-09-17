## Chef Nova
Your AI companion for smarter meals tailored to your pantry, preferences, and diet.

ChefNova is a proposed conversational cooking assistant for people who need help deciding what to cook with available ingredients. Users upload grocery receipts, review the extracted items and quantities, and save them to an inventory database. Before every recipe recommendation, they confirm or edit their current inventory in a table. ChefNova then uses the confirmed groceries and cooking preferences to suggest meals.

This repository contains an existing recipe-assistant prototype. Checkpoint 1 defines the problem, reviews prior work, and proposes the behavior and evaluation that the team will develop further. Proposed capabilities below are design goals, not validated results.

## Team Members & Roles

| Member | Responsibility | Contact |
| --- | --- | --- |
| [Chaitanya Nirantar] | Problem framing, target users, core tasks, and presentation slides 1–3 | [cn32@illinois.edu] |
| [] | Literature synthesis, bibliography, and competitive analysis | [University email] |
| [Aditya Dilip] | Technical approach, Checkpoint 2 validation, and risk analysis | [adityad6@illinois.edu] |
| [Prathamesh Mulay] | Repository organization, project tracking, roadmap, and final submission | [University email] |

Each member will review at least two distinct academic papers, write an individual reflection, and contribute through commits, issues, and pull requests.

## Problem Statement & Motivation

Choosing a meal involves more than finding a recipe. A person must work out whether they have the ingredients, whether the meal matches their preferences, and whether the instructions fit their time, equipment, and cooking experience. For a student or beginner cook, checking these conditions across several recipes can make a simple dinner decision feel complicated.

Consider a student with rice, chickpeas, and spinach who wants a vegetarian dinner in about 20 minutes. Finding a recipe is only the beginning: they still need to identify missing ingredients, decide which substitutions are reasonable, and understand the cooking steps. ChefNova focuses on this gap between discovering a recipe and choosing a meal that feels practical to prepare.

Our working hypothesis is that an assistant grounded in a user's stated ingredients and constraints can reduce the effort of choosing a meal. We will investigate this hypothesis through literature review and prototype evaluation; we do not yet claim reductions in food waste, spending, or preparation time.

The project is timely because conversational AI offers an interaction model in which users can state several constraints together and revise them in follow-up messages. The research question is whether this flexibility can produce useful, understandable suggestions while preserving the user's constraints.

## Target Users & Core Tasks

These are initial design personas to validate, not findings from completed user research.

| Target user | Situation | Need |
| --- | --- | --- |
| College student cooking at home | Has a small pantry, a busy schedule, and limited cooking equipment | Find a feasible meal without comparing many recipes manually |
| Beginner home cook | Has ingredients but is unsure how to combine them or adapt instructions | Receive clear steps and understandable substitutions |
| Home cook with dietary preferences | Wants suggestions that consistently reflect stated preferences | Refine a meal without repeatedly restating constraints |

### 1. Build an inventory from grocery receipts

The user uploads a grocery receipt image. ChefNova extracts grocery names, quantities, and units into an editable table. The user corrects uncertain entries before adding them to a persistent inventory database. Prices are not quantities, and unknown package sizes require clarification.

**Desired outcome:** The user has a saved inventory with reviewed item names, quantities, and units.

### 2. Confirm or correct quantities before recommendations

Whenever the user requests a recipe, ChefNova displays the stored inventory. The user confirms quantities or edits items that have been consumed, added, or discarded. Recipe recommendations begin only after confirmation.

**Desired outcome:** Recommendations use current, user-confirmed quantities instead of assuming purchased groceries are still available.

### 3. Get recipes from the confirmed inventory

ChefNova recommends meals using confirmed ingredients and quantities along with dietary preferences. Recommendations should explain preparation steps and identify additional ingredients or quantities needed. Quantity feasibility is an evaluation target, not a guarantee from generated text.

**Desired outcome:** The user understands the next cooking action and can identify any remaining uncertainty.

### Initial definition of success

Evaluation should examine receipt extraction accuracy, quantity/unit errors, the effort of correcting inventory, whether confirmation occurs before every recommendation, whether users can select a meal, whether suggestions preserve explicit constraints, whether missing ingredients are visible, and whether instructions are understandable. Completion time, constraint violations, and user feedback are candidate measures; Person 3 will define the test cases and acceptance thresholds for Checkpoint 2.

## Competitive Landscape

**Person 2 to complete:** Compare 2–3 named existing systems using verified sources and connect the comparison to the academic literature. Investigate ingredient-based discovery, conversational revision, explanation quality, and preservation of dietary constraints. Do not assume these capabilities are absent from existing tools.

## Initial Concept & Value Proposition

ChefNova brings receipt-based grocery entry, a persistent quantity inventory, mandatory inventory review, and recipe recommendations into one interaction. A receipt records a purchase, not what remains today; the confirmation step keeps users in control of that distinction. Its intended value is helping a user move from “What can I cook?” to a practical meal choice with understandable instructions.

GenAI's proposed role is to extract and normalize grocery receipt entries, interpret informal requests, and explain meal suggestions. Structured database operations handle quantities and persistence, while users resolve uncertain extraction results. Person 3 will specify which operations require generation, which use retrieved recipe data, and which need explicit validation. The prototype's dietary filtering is not evidence of verified allergy safety, and generated nutrition values must not be presented as measured facts.

## Milestones Roadmap

**Draft for Person 4 to finalize with course dates and later-checkpoint requirements.**

| Checkpoint | Planned outcome |
| --- | --- |
| 1 | Problem definition, 8+ academic papers, individual reflections, 500–800-word proposal, GitHub board, and kickoff presentation |
| 2 | Validate core prompt or agent logic using representative meal requests and constraint-conflict cases |
| 3 | Proposed: refine the integrated prototype using evaluation findings; confirm against the official assignment |
| 4 | Proposed: deliver the final demonstration and evaluation summary; confirm against the official assignment |

## Grocery Workflow

Upload receipt → Review extracted groceries → Save quantities → Request a recipe → Confirm/edit inventory → Recommend recipes.

The prototype accepts PNG/JPG receipt images and stores groceries in local SQLite. Identical receipt bytes are deduplicated per user; rescanned receipts may still need manual correction. Matching names and units are added together; different units remain separate. Receipt images are sent to Gemini and are not persisted locally. User names identify local profiles, but are not authentication. Automatic consumption tracking is outside the initial scope.
