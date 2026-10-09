# CP2 Individual Reflection — Ananya Jandhyala

## Role

Gap Analysis & Theory

## Prompting study notes

I reviewed the team's 12 prompting scenarios designed to test ChefNova across
reasoning, memory, attention, and meta-coordination. The scenarios included
typical, edge, and failure cases involving receipt extraction, abbreviated receipt
lines, unknown package sizes, dietary constraints, explicit exclusions, missing
core ingredients, optional ingredients, substitutions, decision rights, constraint
overload, stale inventory, and source faithfulness.

The prompting study showed that ChefNova's main reliability problem is not simply
obvious hallucination. In several cases, the model understood the correct rule but
still silently filled gaps when applying it.

For example, in T01 the model correctly avoided inventing quantities that were not
visible on the receipt. However, T02 showed a more subtle reasoning failure:
conflicting receipt descriptors such as "WHL" and "2%" were merged into a confident
interpretation instead of preserving the ambiguity for user review.

T10 and T11 exposed a related problem with hidden dependencies. The model produced
recommendations that sounded feasible while assuming preparation state or
ingredients that had not actually been confirmed, such as cooked rice, oil, or
seasonings.

T08 also showed a trust-calibration issue. The model approved a substitution
without first establishing enough recipe context, which could encourage a user to
over-trust a fluent recommendation.

My main takeaway from the prompting study is that a model stating the correct rule
is not enough. ChefNova needs structured application logic around the generative
model to verify inventory, hard constraints, missing ingredients, equipment, and
other dependencies before presenting a recipe as feasible.

Platform evidence and detailed outputs are recorded in the team's validation
transcripts. The ChatGPT run contained all 12 scenarios. The prompting evidence
that most influenced my reflection was T02, T08, T10, and T11 because these cases
showed how ambiguity, over-confidence, hidden dependencies, and stale inventory can
break the human-AI handoff.

## Speed-dating interviews

### Interview 1

- **Participant:** Graduate student who cooks approximately 3–4 times per week and
  usually decides what to cook based on groceries already available.
- **Task shown:** ChefNova's pantry-first concept, including receipt extraction,
  inventory confirmation, recipe recommendations, and conversational refinement.
- **Main finding:** Users want AI assistance with inventory and recommendations,
  but do not want the AI to independently determine persistent pantry truth.
  Receipt extraction can assist the user, but extracted items should be reviewed
  before being saved. The participant also emphasized that inventory maintenance
  must remain lightweight or the system could create more work than simply
  searching for recipes.
- **Quote:** The participant's interview notes emphasized that saying
  "I don't have spinach" should affect the current recommendations but should not
  automatically delete spinach from the saved pantry.
- **Complementarity interpretation:** This is a meta-coordination and
  role-partitioning issue. AI can interpret receipts and conversational updates,
  but the human should retain decision rights over persistent inventory state.
- **Design implication:** AI suggestion → user review → explicit confirmation →
  persistent inventory update. Temporary conversational exclusions should not
  silently modify saved inventory.

> Note: The repository's Pilot Interview 1 record does not identify the interviewer.
> I am using it here as team validation evidence rather than claiming that I
> personally conducted the interview.

### Interview 2

- **Participant:** Experienced home cook and working professional who enjoys
  preparing elaborate meals on weekends and frequently cooks for family members.
- **Task shown:** The ChefNova concept of using AI, pantry information, and user
  preferences to recommend appropriate meals.
- **Main finding:** The interview challenged our assumption that users primarily
  want to cook from ingredients they already have. This participant often decides
  on a particular meal first and then purchases the ingredients required to make
  it. The interview also exposed a multi-person planning problem: the person using
  ChefNova may be cooking for people with very different preferences and
  constraints. In this case, one family member dislikes cilantro, another enjoys
  seafood, and another has a peanut allergy, while the participant and his wife
  are generally flexible.
- **Quote:** Paraphrased from interview notes: the participant described weekend
  cooking as choosing the meal he wants to prepare and getting the particular
  ingredients needed for it, rather than limiting the decision to what is already
  in the refrigerator.
- **Complementarity interpretation:** The human should define the cooking goal,
  who is eating, and which constraints are non-negotiable. AI can then interpret
  those requirements, generate candidates, identify missing ingredients, and
  explain trade-offs. A dislike such as cilantro can influence ranking, whereas a
  peanut allergy must function as a hard safety constraint that the AI cannot
  relax.
- **Design implication:** ChefNova should support different cooking intentions,
  including a pantry-first "Cook Now" workflow and a goal-first "Plan a Meal"
  workflow. The system should also distinguish hard constraints such as allergies
  from soft preferences and could support household or guest profiles for
  multi-person meal planning.

## Finding that changed or confirmed my assumption

The finding that most changed my assumption came from Interview 2. Our original
concept was largely pantry-first. I assumed ChefNova's main value would come from
answering the question, "What can I cook with what I already have?" and optimizing
recommendations around confirmed inventory.

The interview showed that this is not universal. An experienced home cook may
begin with the opposite workflow: decide on an elaborate meal first and then
purchase the ingredients necessary to prepare it. For this user, minimizing
shopping is not necessarily the objective.

The interview also showed that the person interacting with ChefNova may not be the
only person eating the meal. This introduces different levels of constraints. A
cilantro dislike is a soft preference, while a peanut allergy is a non-negotiable
safety constraint.

This finding connects to Gonzalez et al.'s complementarity framework through
meta-coordination and role partitioning. The human and AI should not have the same
decision rights. The human should establish the goal, diners, ground truth, and
non-negotiable constraints. AI is better suited to interpreting those inputs,
searching the recipe space, generating candidates, identifying missing
ingredients, and explaining trade-offs.

It also relates to trust calibration. A fluent or highly ranked AI recommendation
should not cause the user to assume that every important constraint has been
satisfied. Hard constraints need to be represented and enforced explicitly rather
than relying only on the model to remember them conversationally.

My assumption therefore changed from "ChefNova should optimize for what is already
in the pantry" to "ChefNova should first understand the user's cooking intent and
constraints, then optimize within that context."

## How this affected the design

The finding suggests that ChefNova should not be limited to a single pantry-first
workflow.

The first design direction is **Cook Now**. In this mode, ChefNova starts with the
user's confirmed inventory and prioritizes meals that can be prepared immediately
or with minimal additional shopping. Inventory feasibility, available equipment,
and hard dietary constraints determine which recipes qualify.

The second design direction is **Plan a Meal**. In this mode, the user can begin
with a dish, cuisine, occasion, or more elaborate cooking goal. ChefNova can then
recommend appropriate recipes, account for the people eating the meal, and
identify which ingredients need to be purchased.

The interview also motivates a future **household or guest profile** capability.
Users could specify who is eating a particular meal, allowing ChefNova to combine
requirements across diners. Importantly, the system should represent these
requirements differently: allergies and dietary restrictions should operate as
hard filters, while dislikes and preferences should influence ranking.

The responsibility split should therefore remain explicit:

- **Human:** Confirms inventory, defines cooking intent, identifies diners, and
  establishes non-negotiable constraints.
- **Application logic:** Enforces hard constraints, inventory state, equipment
  requirements, and feasibility checks.
- **Generative AI:** Interprets natural-language requests, generates candidate
  recipes, supports refinement, and explains recommendations.

This design preserves human-AI complementarity because the AI contributes where
generation and interpretation are useful without being given authority to silently
change ground truth or relax safety-critical constraints.
