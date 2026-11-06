"""Recipe recommendation tests. Model responses are fixtures. No network."""

import json

from app.recipe_recommendations import (
    RECIPE_MODEL,
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
    assert [card["status"] for card in cards] == ["Check quantities", "Almost ready", "Needs shopping"]
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
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
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
    assert cards[0]["status"] == "Check quantities"
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
    data = json.loads(prompt)
    assert data["pantry"] == [{"ingredient": "Spinach", "quantity": 1, "unit": "bag"}]
    assert data["hard_constraints"] == {"diet": "Vegan", "max_minutes": 20, "avoid": ["peanut"]}
    assert data["preferences"]["meal_request"] == "a quick bowl"
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


def test_provider_order_and_fallback(monkeypatch):
    import app.recipe_recommendations as module

    calls = []
    def groq(key, prompt, *, timeout):
        calls.append("groq")
        raise RuntimeError("Service unavailable")
    def gemini(key, prompt, *, timeout):
        calls.append("gemini")
        return _payload([_recipe("Rice", ["Rice"])])
    monkeypatch.setattr(module, "groq_complete", groq)
    monkeypatch.setattr(module, "gemini_complete", gemini)
    result = recommend_recipes([{"Ingredient": "Rice"}], Constraints(), api_key="gemini-key", groq_api_key="groq-key")
    assert result.ok and calls == ["groq", "gemini"]
    assert result.notice and "Gemini" in result.notice
    assert result.candidates[0]["source"] == f"Gemini {RECIPE_MODEL}"


def test_groq_only_and_success_skips_gemini(monkeypatch):
    import app.recipe_recommendations as module

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setattr(module, "groq_complete", lambda key, prompt, **kwargs: _payload([_recipe("Rice", ["Rice"])]))
    def unexpected(*args):
        raise AssertionError("Gemini should not be called")
    monkeypatch.setattr(module, "gemini_complete", unexpected)
    for key in (None, "gemini-key"):
        result = recommend_recipes([{"Ingredient": "Rice"}], Constraints(), api_key=key)
        assert result.ok and result.notice is None
        assert result.candidates[0]["source"].startswith("Groq ")


def test_invalid_groq_output_falls_back_but_valid_empty_list_does_not(monkeypatch):
    import app.recipe_recommendations as module

    calls = []
    monkeypatch.setattr(module, "gemini_complete", lambda *args, **kwargs: calls.append("gemini") or '{"recipes": []}')
    for raw, expected_calls in (("not json", ["gemini"]), ('{"recipes": []}', [])):
        calls.clear()
        monkeypatch.setattr(module, "groq_complete", lambda *args, **kwargs: raw)
        result = recommend_recipes([{"Ingredient": "Rice"}], Constraints(), api_key="gemini-key", groq_api_key="groq-key")
        assert result.ok and result.candidates == []
        assert calls == expected_calls


def test_all_providers_fail_without_exposing_keys(monkeypatch):
    import app.recipe_recommendations as module

    def fail(key, prompt, *, timeout):
        raise RuntimeError(f"Unauthorized key: {key}")
    monkeypatch.setattr(module, "groq_complete", fail)
    monkeypatch.setattr(module, "gemini_complete", fail)
    result = recommend_recipes([{"Ingredient": "Rice"}], Constraints(), api_key="gemini-secret", groq_api_key="groq-secret")
    assert not result.ok and not result.candidates
    assert "Groq" in result.error and "Gemini" in result.error
    assert "secret" not in result.error


def test_groq_complete_sends_schema_and_closes_client():
    from types import SimpleNamespace
    from app.recipe_recommendations import GROQ_RECIPE_MODEL, groq_complete

    calls = {}
    observed_usage = []
    def create(**kwargs):
        calls.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content='{"recipes": []}'))],
            usage=SimpleNamespace(prompt_tokens=800, completion_tokens=900),
        )
    class Client:
        chat = SimpleNamespace(completions=SimpleNamespace(create=create))
        def close(self):
            calls["closed"] = True
    def factory(**kwargs):
        calls["settings"] = kwargs
        return Client()
    assert groq_complete("session-key", "pantry prompt", client_factory=factory, usage_callback=observed_usage.append) == '{"recipes": []}'
    assert observed_usage == [{"input_tokens": 800, "output_tokens": 900}]
    assert calls["model"] == GROQ_RECIPE_MODEL
    assert calls["response_format"] == {"type": "json_object"}
    assert "recipes" in calls["messages"][0]["content"]
    assert calls["messages"][1]["content"] == "pantry prompt"
    assert calls["settings"]["timeout"] == 20.0 and calls["settings"]["max_retries"] == 0
    assert calls["closed"]


def test_gemini_usage_includes_thinking_tokens():
    from types import SimpleNamespace

    response = SimpleNamespace(parsed=None, text='{"recipes": []}', usage_metadata=SimpleNamespace(
        prompt_token_count=800, candidates_token_count=700, thoughts_token_count=200))
    usage = []
    client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: response), close=lambda: None)
    gemini_complete("key", "prompt", client_factory=lambda key: client,
                    config_builder=lambda: {}, usage_callback=usage.append)
    assert usage == [{"input_tokens": 800, "output_tokens": 900}]



def test_gemini_serializes_recipe_quantity_schema():
    import httpx
    from google import genai
    from google.genai import types

    def respond(request):
        body = json.loads(request.content)
        quantity = (body["generationConfig"]["responseSchema"]["properties"]["recipes"]
                    ["items"]["properties"]["ingredient_amounts"]["items"]["properties"]["quantity"])
        assert quantity["type"] == "NUMBER"
        return httpx.Response(200, json={
            "candidates": [{"content": {"role": "model", "parts": [{"text": '{"recipes": []}'}]}}],
        })

    def factory(key):
        return genai.Client(api_key=key, http_options=types.HttpOptions(
            client_args={"transport": httpx.MockTransport(respond)},
        ))

    assert json.loads(gemini_complete("test-key", "{}", client_factory=factory)) == {"recipes": []}
