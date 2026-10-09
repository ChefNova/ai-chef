# Individual Validation Reflection — Ananya Jandhyala

## Speed-Dating Interview Reflection

One finding from my interview that changed my assumption about ChefNova was that
users do not always begin meal planning by asking, "What can I cook with what I
already have?"

Our original concept was largely pantry-first. We assumed that ChefNova's main
value would come from understanding a user's current inventory and recommending
meals that maximize the ingredients already available.

However, my interview with an experienced home cook challenged this assumption.
The participant enjoys preparing elaborate meals on weekends and often decides
what he wants to cook first, then purchases the specific ingredients required for
that meal. For this user, minimizing grocery shopping is not necessarily the main
goal. The quality and suitability of the planned meal can be more important than
using only ingredients already available.

The interview also revealed a second issue: the person using ChefNova may not be
the only person eating the meal. The participant frequently cooks for family
members with different preferences and constraints. His daughter dislikes
cilantro, his son-in-law enjoys seafood, and his granddaughter has a peanut
allergy, while he and his wife are generally flexible.

This distinction matters because ChefNova should not treat every constraint in the
same way. A dislike such as cilantro can be treated as a soft preference that
affects recipe ranking, while a peanut allergy must be treated as a hard safety
constraint that cannot be overridden by a highly ranked recipe.

## Connection to Human-AI Complementarity

This finding strengthened our use of the complementarity framework from Gonzalez
et al. (2026). The human and AI should not have identical decision rights.

The human should define the meal context: who is eating, what constraints are
non-negotiable, and whether the goal is to use existing ingredients or plan a
specific meal. ChefNova can then use AI for tasks where it adds value, such as
interpreting natural-language requests, generating recipe candidates, identifying
missing ingredients, and explaining trade-offs.

This is also a meta-coordination and role-partitioning problem. The AI should
operate within boundaries established by the user rather than deciding which
constraints can be relaxed. In particular, safety-critical constraints such as
allergies should be enforced before recipe ranking rather than treated as ordinary
preferences.

## How This Changes the Design

Based on this finding, I would refine ChefNova to support two different cooking
intentions:

1. **Cook Now** — The user wants to make something primarily from ingredients
   already available. ChefNova prioritizes pantry feasibility and minimizes
   additional shopping.

2. **Plan a Meal** — The user has a dish, cuisine, or more elaborate meal in mind
   and is willing to purchase missing ingredients. ChefNova helps select a suitable
   recipe and identifies what needs to be purchased.

I would also explore household or guest profiles so that the user can specify who
is eating. ChefNova could combine the selected diners' requirements while
distinguishing hard constraints, such as allergies and dietary restrictions, from
soft preferences, such as ingredient dislikes.

The interview therefore changed my assumption from "ChefNova should optimize for
what is already in the pantry" to "ChefNova should first understand the user's
cooking goal and constraints, and then optimize within that context."

## Key Takeaway

My strongest takeaway is that effective human-AI teaming in ChefNova is not simply
about generating better recipes. It is about assigning the right responsibilities
to the human and the AI. The human provides ground truth, intent, and
non-negotiable constraints; ChefNova provides interpretation, search,
recommendations, and explanations within those boundaries.
