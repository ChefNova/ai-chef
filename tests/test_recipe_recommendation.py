"""Recipe recommendation tests. Model responses are fixtures. No network."""

import io
import json
from unittest.mock import patch
from urllib.error import HTTPError

from recipe_recommendation import (
    RECIPE_MODEL,
    RECIPE_SCHEMA,
    Constraints,
    parse_model_output,
    rank_recipes,
    recommend_recipes,
)
from recipe_recommendation.gemini import GeminiRecipeModel
from recipe_recommendation.schema import RECIPE_PROMPT, THINKING_LEVEL


class FakeModel:
    def __init__(self, raw):
        self.raw = raw
        self.calls = []
        self.model_used = "fake"

    def recommend(self, prompt):
        self.calls.append(prompt)
        if isinstance(self.raw, Exception):
            raise self.raw
        return self.raw


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
    raw = _payload(
        [
            _recipe("Chicken Bowl", ["Chicken", "Rice"], diet="Vegetarian"),
            _recipe("Plain Rice", ["Rice"], diet="Vegan"),
            _recipe("Any Rice", ["Rice"], diet="Omnivore"),
        ]
    )
    parsed = parse_model_output(raw)
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
    model = FakeModel(_payload([_recipe("Rice", ["Rice"])]))
    result = recommend_recipes([], Constraints(diet="Vegan"), model)
    assert result.ok is False
    assert result.candidates == []
    assert model.calls == []
    assert "invented" in result.error


def test_inconsistent_ingredients_return_no_recipes():
    raw = _payload(
        [
            _recipe(
                "Rice Bowl",
                ["Rice"],
                substitutions=[{"ingredient": "Chicken", "instead": "mushrooms"}],
            )
        ]
    )
    parsed = parse_model_output(raw)
    assert parsed.ok is False
    assert parsed.candidates == []
    assert "inconsistent" in parsed.error


def test_partial_recipe_is_shown_with_missing_fields_marked():
    raw = _payload(
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
    parsed = parse_model_output(raw)
    cards = rank_recipes(
        parsed.candidates,
        Constraints(),
        [{"Ingredient": "Rice", "Quantity": 1, "Unit": "cups"}],
    )
    assert parsed.ok
    assert cards[0]["status"] == "Cook now"
    assert cards[0]["recipe"]["time"] is None
    assert "minutes" in cards[0]["recipe"]["missing_fields"]
    assert "protein_g" in cards[0]["recipe"]["missing_fields"]
    assert any("Cooking time" in note for note in cards[0]["field_notes"])


def test_time_and_avoid_filters_remove_recipes():
    parsed = parse_model_output(
        _payload(
            [
                _recipe("Quick Rice", ["Rice"], minutes=10),
                _recipe("Slow Stew", ["Rice"], minutes=50),
                _recipe("Peanut Rice", ["Rice", "Peanut butter"], minutes=10),
            ]
        )
    )
    cards = rank_recipes(
        parsed.candidates,
        Constraints(max_minutes=20, avoid=["peanut"]),
        [{"Ingredient": "Rice", "Quantity": 1, "Unit": "cups"}],
    )
    assert [card["recipe"]["title"] for card in cards] == ["Quick Rice"]


def test_prompt_includes_pantry_and_hard_filters_without_calling_network():
    model = FakeModel(_payload([_recipe("Rice", ["Rice"])]))
    pantry = [{"Ingredient": "Spinach", "Quantity": 1, "Unit": "bag"}]
    result = recommend_recipes(
        pantry,
        Constraints(diet="Vegan", max_minutes=20, avoid=["peanut"], request="a quick bowl"),
        model,
    )
    assert result.ok
    prompt = model.calls[0]
    assert "Spinach" in prompt
    assert "Diet hard filter: Vegan" in prompt
    assert "Maximum minutes: 20" in prompt
    assert "peanut" in prompt
    assert "a quick bowl" in prompt
    assert RECIPE_PROMPT in prompt


def test_gemini_recipe_request_sends_schema_without_opening_a_real_socket(monkeypatch):
    monkeypatch.delenv("GEMINI_RECIPE_MODEL", raising=False)
    captured = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            body = {"recipes": [_recipe("Rice", ["Rice"])]}
            return json.dumps(
                {"candidates": [{"content": {"parts": [{"thought": True, "text": "planning"}, {"text": json.dumps(body)}]}}]}
            ).encode()

    def _urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode())
        captured["headers"] = {key.lower(): value for key, value in request.header_items()}
        return _Response()

    with patch("recipe_recommendation.gemini.urlopen", _urlopen):
        model = GeminiRecipeModel(api_key="test-key-not-real")
        raw = model.recommend("pantry prompt")

    parsed = parse_model_output(raw)
    assert parsed.ok and parsed.candidates[0]["title"] == "Rice"
    config = captured["body"]["generationConfig"]
    assert config["responseFormat"]["text"]["schema"] == RECIPE_SCHEMA
    assert config["responseFormat"]["text"]["mimeType"] == "APPLICATION_JSON"
    assert config["thinkingConfig"]["thinkingLevel"] == THINKING_LEVEL
    assert "temperature" not in config
    assert f"/models/{RECIPE_MODEL}:generateContent" in captured["url"]
    assert captured["headers"]["x-goog-api-key"] == "test-key-not-real"
    assert "test-key-not-real" not in captured["url"]
    assert "test-key-not-real" not in json.dumps(captured["body"])


def test_gemini_recipe_http_error_does_not_invent_recipes():
    secret = "test-key-not-real"

    def _urlopen(request, timeout):
        body = {"error": {"code": 400, "message": f"bad request key={secret}", "status": "INVALID_ARGUMENT"}}
        raise HTTPError(
            request.full_url,
            400,
            "Bad Request",
            hdrs=None,
            fp=io.BytesIO(json.dumps(body).encode()),
        )

    with patch("recipe_recommendation.gemini.urlopen", _urlopen):
        model = GeminiRecipeModel(api_key=secret, model=RECIPE_MODEL)
        result = recommend_recipes(
            [{"Ingredient": "Rice", "Quantity": 1, "Unit": "cups"}],
            Constraints(),
            model,
        )

    assert result.ok is False
    assert result.candidates == []
    assert "HTTP 400" in result.error
    assert secret not in result.error
    assert "key=[redacted]" in result.error
