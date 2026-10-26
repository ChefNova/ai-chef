"""Recipe recommendation tests. Model responses are fixtures. No network."""

import json

from app.recipe_recommendations import (
    RECIPE_MODEL,
    RECIPE_PROMPT,
    Constraints,
    gemini_complete,
    parse_model_output,
    rank_recipes,
    recommend_recipes,
)


def _recipe(title, ingredients, diet="Vegan", minutes=15, substitutions=None, missing_fields=None, protein=12):
    return {
        "title": title,
        "minutes": minutes,
        "protein_g": protein,
        "diet": diet,
        "cuisine": "Mediterranean",
        "emoji": "🥗",
        "tags": ["Pantry"],
        "ingredients": ingredients,
        "instructions": [f"Cook the {title.lower()}."],
        "substitutions": substitutions or [],
        "missing_fields": missing_fields or [],
    }


def _payload(recipes):
    return json.dumps({"recipes": recipes})


def test_diet_violations_are_dropped_and_a_valid_recipe_remains():
    parsed = parse_model_output(
        _payload(
            [
                _recipe("Chicken Bowl", ["Chicken", "Rice"], diet="Vegetarian"),
                _recipe("Plain Rice", ["Rice"], diet="Vegan"),
                _recipe("Any Rice", ["Rice"], diet="Omnivore"),
            ]
        )
    )
    cards = rank_recipes(
        parsed.candidates,
        Constraints(diet="Vegan"),
        [{"Ingredient": "Rice", "Quantity": 1, "Unit": "cups"}],
    )
    assert [card["recipe"]["title"] for card in cards] == ["Plain Rice"]


def test_pantry_matching_assigns_cook_almost_and_shopping_buckets():
    parsed = parse_model_output(
        _payload(
            [
                _recipe("Spinach Rice", ["Rice", "Spinach"]),
                _recipe("Lemon Rice", ["Rice", "Spinach", "Lemon"]),
                _recipe("Market Bowl", ["Rice", "Tofu", "Lemon", "Ginger"]),
            ]
        )
    )
    pantry = [
        {"Ingredient": "Rice", "Quantity": 2, "Unit": "cups"},
        {"Ingredient": "Spinach", "Quantity": 1, "Unit": "bag"},
    ]
    cards = rank_recipes(parsed.candidates, Constraints(), pantry)
    assert [card["status"] for card in cards] == ["Cook now", "Almost ready", "Needs shopping"]
    assert cards[0]["missing"] == []
    assert cards[1]["missing"] == ["Lemon"]
    assert cards[2]["score"] < cards[1]["score"] < cards[0]["score"]


def test_invalid_json_returns_no_recipes():
    parsed = parse_model_output("not json")
    assert parsed.ok is False
    assert parsed.candidates == []
    assert "valid JSON" in parsed.error

    listed = parse_model_output(json.dumps([{"title": "Rice"}]))
    assert listed.ok is False
    assert listed.candidates == []


def test_empty_pantry_does_not_call_the_model():
    calls = []

    def complete(prompt):
        calls.append(prompt)
        return _payload([_recipe("Rice", ["Rice"])])

    result = recommend_recipes([], Constraints(diet="Vegan"), api_key="present", complete=complete)
    assert result.ok is False
    assert result.candidates == []
    assert calls == []
    assert "invented" in result.error


def test_missing_key_does_not_call_the_model(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    calls = []

    def complete(prompt):
        calls.append(prompt)
        return _payload([_recipe("Rice", ["Rice"])])

    result = recommend_recipes(
        [{"Ingredient": "Rice", "Quantity": 1, "Unit": "cups"}],
        Constraints(),
        api_key="",
        complete=complete,
    )
    assert result.ok is False
    assert result.candidates == []
    assert calls == []
    assert "Nothing was sent" in result.error


def test_inconsistent_ingredients_return_no_recipes():
    parsed = parse_model_output(
        _payload(
            [
                _recipe(
                    "Rice Bowl",
                    ["Rice"],
                    substitutions=[{"ingredient": "Chicken", "instead": "mushrooms"}],
                )
            ]
        )
    )
    assert parsed.ok is False
    assert parsed.candidates == []
    assert "inconsistent" in parsed.error


def test_partial_recipe_is_shown_with_missing_fields_marked():
    parsed = parse_model_output(
        _payload(
            [
                {
                    "title": "Rice Bowl",
                    "minutes": None,
                    "protein_g": None,
                    "diet": "Vegan",
                    "cuisine": None,
                    "emoji": None,
                    "tags": [],
                    "ingredients": ["Rice"],
                    "instructions": ["Steam the rice."],
                    "substitutions": [],
                    "missing_fields": ["minutes", "protein_g"],
                }
            ]
        )
    )
    cards = rank_recipes(
        parsed.candidates,
        Constraints(),
        [{"Ingredient": "Rice", "Quantity": 1, "Unit": "cups"}],
    )
    assert parsed.ok
    assert cards[0]["status"] == "Cook now"
    assert cards[0]["recipe"]["time"] is None
    assert "minutes" in cards[0]["recipe"]["missing_fields"]
    assert any("Cooking time" in note for note in cards[0]["field_notes"])


def test_prompt_includes_pantry_and_hard_filters():
    seen = []

    def complete(prompt):
        seen.append(prompt)
        return _payload([_recipe("Rice", ["Rice"])])

    result = recommend_recipes(
        [{"Ingredient": "Spinach", "Quantity": 1, "Unit": "bag"}],
        Constraints(diet="Vegan", max_minutes=20, avoid=["peanut"], request="a quick bowl"),
        api_key="not-a-real-key",
        complete=complete,
    )
    assert result.ok
    prompt = seen[0]
    assert "Spinach" in prompt
    assert "Diet hard filter: Vegan" in prompt
    assert "Maximum minutes: 20" in prompt
    assert "peanut" in prompt
    assert "a quick bowl" in prompt
    assert RECIPE_PROMPT in prompt
    assert "not-a-real-key" not in prompt


def test_gemini_complete_uses_the_receipt_client_and_flash_lite():
    calls = {}

    class _Models:
        @staticmethod
        def generate_content(model, contents, config):
            calls["model"] = model
            calls["contents"] = contents
            calls["config"] = config

            class _Response:
                parsed = None
                text = _payload([_recipe("Rice", ["Rice"])])

            return _Response()

    class _Client:
        models = _Models()

        def close(self):
            calls["closed"] = True

    def factory(key):
        calls["key"] = key
        return _Client()

    def config_builder():
        return {"response_mime_type": "application/json", "response_schema": "RecipeList"}

    raw = gemini_complete(
        "session-key",
        "pantry prompt",
        client_factory=factory,
        config_builder=config_builder,
    )
    parsed = parse_model_output(raw)
    assert parsed.ok and parsed.candidates[0]["title"] == "Rice"
    assert calls["key"] == "session-key"
    assert calls["model"] == RECIPE_MODEL
    assert calls["contents"] == "pantry prompt"
    assert calls["config"]["response_mime_type"] == "application/json"
    assert calls["closed"] is True
    assert "session-key" not in json.dumps(calls["config"])
