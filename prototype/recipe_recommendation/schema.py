"""Prompt, response schema, and model settings for recipe ranking."""

RECIPE_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODELS = ("gemini-3.1-flash-lite",)
THINKING_LEVEL = "low"
TIMEOUT_SECONDS = 30

RECIPE_PROMPT = """You propose recipes a home cook can make from a confirmed pantry.

Rules:
- Return only JSON that matches the schema. No markdown and no prose.
- Use the confirmed pantry as the food the cook already has. Do not claim they have anything else.
- A recipe may include extra ingredients. Those are shopping items, not pantry items.
- Diet, maximum minutes, and avoid-ingredients are hard limits. Do not return a recipe that breaks them.
- Diet must be exactly Vegetarian, Vegan, or Omnivore. Vegetarian recipes contain no meat, poultry, or seafood. Vegan recipes also contain no eggs, dairy, or honey.
- Ingredients are grocery names only, such as "chickpeas" or "spinach". Do not put amounts, prices, or choices inside one ingredient name.
- Do not repeat an ingredient. Every substitution must name one of that recipe's ingredients.
- If you do not know minutes, protein_g, cuisine, or an emoji, use null and list the unknown field in missing_fields. Do not guess a number.
- If you know the field, do not list it in missing_fields.
- Return at most 4 recipes. If none can follow the hard limits, return an empty recipes array.
"""

# Gemini 3 responseFormat uses JSON Schema. Nulls are a type union.
RECIPE_SCHEMA = {
    "type": "object",
    "required": ["recipes"],
    "properties": {
        "recipes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "title",
                    "minutes",
                    "protein_g",
                    "diet",
                    "cuisine",
                    "emoji",
                    "tags",
                    "ingredients",
                    "instructions",
                    "substitutions",
                    "missing_fields",
                ],
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "minutes": {"type": ["integer", "null"]},
                    "protein_g": {"type": ["integer", "null"]},
                    "diet": {"type": ["string", "null"]},
                    "cuisine": {"type": ["string", "null"]},
                    "emoji": {"type": ["string", "null"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "ingredients": {"type": "array", "items": {"type": "string"}},
                    "instructions": {"type": "array", "items": {"type": "string"}},
                    "substitutions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["ingredient", "instead"],
                            "properties": {
                                "ingredient": {"type": "string"},
                                "instead": {"type": "string"},
                            },
                        },
                    },
                    "missing_fields": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["title", "minutes", "protein_g", "diet", "ingredients", "instructions"],
                        },
                    },
                },
            },
        },
    },
}
