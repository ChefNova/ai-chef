# ChefNova recipe generation and ranking

The runtime prompt and response models live in [recipe_recommendations.py](../recipe_recommendations.py). The application sends confirmed pantry quantities, selected constraints, and optional meal preferences as structured input.

| Step | Current implementation |
| --- | --- |
| Primary candidate generation | Groq, default `openai/gpt-oss-120b` with a `GROQ_RECIPE_MODEL` override. JSON object mode, temperature 0.2, and a 3,000 completion-token limit. |
| Fallback candidate generation | Gemini `gemini-3.5-flash-lite` with the `RecipeList` response schema and low thinking. The runtime leaves temperature at the provider default. |
| Filtering and ranking | Python `rank_recipes()` applies diet, maximum time, and avoid filters. It orders the survivors using pantry match, missing ingredients, cooking time, or protein according to the selected priority. This step makes zero provider calls. |

## Output contract

The model returns a JSON object with a `recipes` array and is asked for at most four candidates. Each candidate can include a title, estimated time, protein, diet, cuisine, tags, ingredients, ingredient amounts, instructions, substitutions, and missing fields.

- Ingredient names are separate from quantities. Each entry in `ingredient_amounts` identifies the ingredient, quantity, and unit. Unknown amounts can be omitted.
- Substitutions use `ingredient` and `instead` fields. The original ingredient must appear in the recipe's ingredient list.
- A recipe can require extra ingredients. Local validation uses the confirmed pantry to flag missing items, insufficient stock, and quantities that need review.
- A valid `{"recipes":[]}` response ends generation. An invalid response can trigger the fallback provider.

The initial results view shows up to three locally ranked recipes. See the [recipe pipeline guide](../RECIPE_RECOMMENDATIONS.md) and [safety and privacy guide](../../docs/safety_privacy.md).
