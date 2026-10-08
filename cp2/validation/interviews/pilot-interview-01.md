# Interview 1
# Inteviewer: Chaitanya Nirantar

 Participant is a graduate student who cooks 3–4 times a week and usually decides from groceries already on hand. 

## 1. Accuracy and hallucinations

The participant said they would not trust ChefNova to automatically add receipt-extracted items to inventory, because receipts often contain abbreviations and non-food products. They preferred reviewing and correcting detected items before those items become part of the confirmed pantry.

**Key finding:** AI extraction can be useful, but users should verify the result.

**Design implication:** Receipt upload → AI extraction → review/edit → confirm inventory.

## 2. Reliability and consistency

The participant expected ChefNova to remember important constraints throughout the interaction. If they say spinach is no longer available, later recipes should not require spinach. Dietary restrictions such as vegetarian preferences should stay active for the session.

**Key finding:** Losing previously stated constraints would quickly reduce trust.

**Design implication:** Maintain structured state for inventory and hard preferences instead of depending only on conversational memory.

## 3. Latency and performance

Comfortable waiting about 5–10 seconds for heavier work such as receipt processing. Conversational recipe refinement should feel much faster. Waiting about 30 seconds after every preference change would be frustrating.

**Key finding:** Moderate latency is acceptable for complex processing; conversation should stay quick.

**Design implication:** Progress feedback on slow tasks; keep recommendation refinement responsive.

## 4. UX friction

Preferred several ways to add groceries: receipt upload after shopping, manual text for individual items, and voice for quick updates. Inventory maintenance was called out as a major risk. If every consumed item must be updated by hand, ChefNova could be more work than searching for recipes.

**Key finding:** Accurate inventory has to take very little effort.

**Design implication:** Support receipt, text, and voice, and make corrections fast.

## 5. Safety, guardrails, and decision rights

The participant did not want ChefNova to permanently change inventory from an AI inference or a conversational aside. “I don’t have spinach” may drop spinach recipes from the current recommendations, but the app should ask before deleting spinach from the saved pantry.

**Key finding:** The user wants final authority over persistent inventory.

**Theoretical connection:** Meta-coordination / role partitioning.

**Design implication:** The AI proposes changes; the human confirms anything that persists.

## 6. Cost and efficiency

Valuable if it saves time versus searching Google or YouTube. The benefit disappears if inventory upkeep or correcting AI mistakes costs too much effort.

**Key finding:** ChefNova has to save more effort than it creates.

**Design implication:** Automate repetitive work and keep user control over important facts.

## 7. Recipe feasibility

A recipe missing one small or optional item (lemon, a garnish) can still be useful. A recipe missing a core ingredient (chicken for a chicken dish) should not be shown as immediately cookable.

**Key finding:** Missing ingredients should not all be treated the same.

**Design implication:** Classify ingredients as required, optional, or substitutable. Label recipes Cook Now, Almost Ready, or Needs Shopping.

## 8. Trust and recommendation explanations

Trust increases if the app says why a recipe was recommended: ingredients already available, 18 minutes, vegetarian, high protein. A recipe with no explanation feels like a generic chatbot.

**Key finding:** Transparent explanations improve trust.

**Design implication:** Each recommendation includes a short “Why this recipe?” note.

## 9. Recipe match scores

A score such as “94% ChefNova Match” helps only if it is explained. A bare number can look arbitrary.

**Key finding:** Numeric scores need transparency.

**Design implication:** If a match score is shown, also show pantry match, dietary match, cooking time, and protein preference.

## 10. Biggest concern

Keeping inventory accurate. If the user must constantly report purchases, consumption, expiry, and discards, they may stop using the system.

**Key finding:** Inventory maintenance may be ChefNova’s biggest UX challenge.

**Design implication:** Lightweight updates through conversation, receipt scanning, quick edits, and confirmation, rather than extensive manual management.

## Main findings

1. Users want AI assistance without giving the AI full control of inventory truth.
2. Receipt-extracted groceries should be reviewed before they are saved.
3. Receipt, text, and voice input are all valuable.
4. Hard constraints such as dietary restrictions should persist reliably.
5. Distinguish required, optional, and substitutable ingredients.
6. Recommendation explanations matter for trust.
7. Match scores should be explainable.
8. Inventory maintenance needs to be extremely lightweight.
9. Persistent changes should require human confirmation.
10. The main value is less effort to decide what to cook from what is already on hand.

## Strongest finding for gap analysis

**Evidence:** The participant did not want ChefNova to automatically modify saved inventory from receipt extraction or conversational inference alone.

**Theory:** Meta-coordination / role partitioning. The AI interprets and recommends; the human keeps authority over pantry truth.

**Design requirement:** AI suggestion → user review → explicit confirmation → persistent inventory update.
