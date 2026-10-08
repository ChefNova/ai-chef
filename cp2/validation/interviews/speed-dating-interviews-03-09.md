# Speed-dating interviews 3–9

These seven notes are records from live speed-dating sessions conducted during CP2 validation. Interview 1 is a separate phone-interview note in `pilot-interview-01.md`. No interview 2 notes were supplied.

## Interview 3 — College student, very limited time

**Participant profile:** Undergraduate student living off campus, cooks 2–3 times a week, usually has only 20–30 minutes for dinner.

**Accuracy and hallucinations:** The participant said they would be frustrated if ChefNova recommended ingredients they did not have, because the main reason for using the app would be to avoid another grocery trip.

**Reliability and consistency:** They expected time limits such as “under 20 minutes” to be treated as strict. If ChefNova repeatedly suggested recipes taking longer, they would stop trusting the recommendations.

**Latency and performance:** They wanted recommendations within a few seconds. Receipt processing could take slightly longer, but recipe suggestions should feel nearly instant.

**UX friction:** They preferred typing something simple such as “rice, eggs, spinach” instead of carefully entering quantity and units every time.

**Safety and guardrails:** They were comfortable with ChefNova suggesting inventory changes but wanted an undo or confirmation option.

**Cost and efficiency:** Saving money was important. They liked the idea of using groceries already at home instead of ordering food.

**Key quote:** “If I still have to go buy three things, then I could have just looked up a recipe myself.”

**Main finding:** Pantry feasibility is more important than recipe variety for time-constrained students.

**Design implication:** Rank Cook Now recipes before recipes requiring additional shopping.

## Interview 4 — College student, shared apartment

**Participant profile:** Graduate student sharing an apartment with two roommates. Some groceries are shared and others are personal.

**Accuracy and hallucinations:** They pointed out that a receipt may contain groceries belonging to different roommates, so receipt extraction alone cannot establish what is personally available.

**Reliability and consistency:** They wanted the app to remember which ingredients were shared versus personal.

**Latency and performance:** They were willing to spend a little more time confirming inventory if it prevented incorrect recommendations later.

**UX friction:** They worried that shared kitchens could make inventory difficult to keep accurate because someone else may consume an ingredient.

**Safety and guardrails:** They did not want ChefNova automatically reducing inventory unless the user explicitly said an ingredient had been consumed.

**Cost and efficiency:** They thought ChefNova could be useful for reducing duplicate grocery purchases in a shared household.

**Key quote:** “Just because something was on my receipt doesn't mean it's still mine or even still in the fridge.”

**Main finding:** Household inventory can have uncertain ownership and availability.

**Design implication:** Treat inventory as user-confirmed state rather than assuming a receipt purchase equals current availability.

## Interview 5 — Beginner cook, low cooking confidence

**Participant profile:** Young professional who recently started cooking and often follows recipes exactly.

**Accuracy and hallucinations:** They were especially concerned about substitutions. They said they would probably trust ChefNova even when they did not know whether a substitution actually made sense.

**Reliability and consistency:** They wanted instructions to remain consistent with the ingredients listed at the beginning of the recipe.

**Latency and performance:** Speed mattered less than getting a clear answer.

**UX friction:** They found cooking terminology confusing and wanted very clear, short steps.

**Safety and guardrails:** They wanted ChefNova to distinguish “safe substitution,” “possible substitution,” and “not recommended” rather than confidently suggesting every replacement.

**Cost and efficiency:** They liked substitutions because buying an entire ingredient for one recipe felt wasteful.

**Key quote:** “If the app tells me sour cream works instead of yogurt, I probably won't know enough to question it.”

**Main finding:** Beginner cooks may over-trust AI-generated cooking advice.

**Design implication:** Show substitution confidence and explain how a substitution changes flavor, texture, or outcome.

## Interview 6 — Beginner cook, minimal kitchen equipment

**Participant profile:** College student living in a small apartment with one pan, one pot, a microwave, and no oven.

**Accuracy and hallucinations:** They said a recipe is not feasible if it requires equipment they do not own, even when all ingredients are available.

**Reliability and consistency:** They wanted equipment preferences to remain active across recommendations.

**Latency and performance:** They preferred receiving three good recipes rather than many options.

**UX friction:** Entering kitchen equipment repeatedly would be annoying.

**Safety and guardrails:** They wanted ChefNova to clearly state when a recipe assumes equipment not recorded in their profile.

**Cost and efficiency:** They would not want to purchase special equipment just to cook a suggested meal.

**Key quote:** “Having all the ingredients doesn't help if the recipe suddenly tells me to put something in an oven.”

**Main finding:** Recipe feasibility depends on both ingredients and equipment.

**Design implication:** Add kitchen-equipment constraints to the user profile and the feasibility check.

## Interview 7 — Diet-aware vegetarian user

**Participant profile:** Graduate student who follows a vegetarian diet but occasionally cooks for friends who eat meat.

**Accuracy and hallucinations:** They considered dietary violations much more serious than ordinary recipe mismatches.

**Reliability and consistency:** Once vegetarian is selected, they expected it to apply automatically to all future recommendations unless explicitly changed.

**Latency and performance:** They preferred correctness over speed for dietary filtering.

**UX friction:** They did not want to repeatedly type “vegetarian” for every request.

**Safety and guardrails:** They wanted dietary restrictions treated as hard constraints rather than recommendation preferences.

**Cost and efficiency:** They liked seeing meals that use pantry ingredients because specialty vegetarian products can be expensive.

**Key quote:** “Vegetarian isn't something the ranking algorithm should decide to ignore because another recipe scores higher.”

**Main finding:** Dietary restrictions should be treated differently from soft preferences.

**Design implication:** Separate hard constraints from soft ranking preferences. Filter vegetarian recipes before ranking.

## Interview 8 — Diet-aware high-protein user

**Participant profile:** Student who regularly goes to the gym and prioritizes higher-protein meals but has no strict dietary restrictions.

**Accuracy and hallucinations:** They were skeptical of AI-generated protein estimates and wanted to know whether numbers came from actual nutrition data.

**Reliability and consistency:** They expected “high protein” to influence ranking but not necessarily eliminate all other recipes.

**Latency and performance:** They were comfortable with a short delay if ChefNova was calculating nutrition from reliable data.

**UX friction:** They wanted simple filters rather than writing detailed nutrition prompts every time.

**Safety and guardrails:** They did not want ChefNova presenting estimated nutrition as exact.

**Cost and efficiency:** They wanted affordable high-protein options using groceries they already owned.

**Key quote:** “If it says 40 grams of protein, I want to know whether that's calculated or just something the AI guessed.”

**Main finding:** Nutrition claims need provenance and uncertainty.

**Design implication:** Nutrition values should come from a reliable database or API and be labeled calculated or estimated rather than invented by the model.

## Interview 9 — Diet-aware user with multiple constraints

**Participant profile:** Young professional who prefers vegetarian meals, avoids dairy, likes spicy food, and usually cooks in under 30 minutes.

**Accuracy and hallucinations:** They said the biggest concern was the model forgetting one constraint when many were provided together.

**Reliability and consistency:** They expected dietary restrictions to persist throughout conversational changes.

**Latency and performance:** They were willing to answer one clarification question if constraints were conflicting.

**UX friction:** Repeating six different preferences every time would make the application tiring to use.

**Safety and guardrails:** They preferred the model to ask a focused clarification rather than guess when requirements conflict.

**Cost and efficiency:** They valued recommendations that fit both dietary needs and existing groceries because specialized ingredients can increase grocery costs.

**Key quote:** “I'd rather it ask me one question than confidently recommend something I specifically said I can't eat.”

**Main finding:** Constraint overload can create both reliability and attention problems.

**Design implication:** Keep a structured profile of persistent constraints and distinguish them from temporary meal preferences.

## Combined findings

| Recurring gap | Who raised it | Requirement |
|---|---|---|
| Recipes require unavailable groceries | Interview 3 | Prioritize Cook Now recipes |
| Receipt does not equal current inventory | Interviews 1 and 4 | User confirms inventory |
| Beginners may over-trust substitutions | Interview 5 | Show substitution confidence |
| Equipment can make recipes infeasible | Interview 6 | Store kitchen-equipment constraints |
| Dietary restrictions can be forgotten | Interview 7 | Hard constraints, applied before ranking |
| Nutrition values may be guessed | Interview 8 | Label the source of a nutrition number |
| Too many constraints may be dropped | Interview 9 | Structured persistent preferences, ask when they conflict |
| Inventory upkeep may become tedious | Interview 1 | Receipt, text, voice, and quick edits |
| Explanations improve confidence | Interview 1 | Show why a recipe was recommended |
| Ambiguity should trigger a question | Interview 9 and ChatGPT T10 | Ask rather than guess |
