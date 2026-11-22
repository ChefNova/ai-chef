"""Track B benchmark plumbing, run with fake providers so no test makes a network call."""

import json

import pytest

import app.recipe_recommendations as rr
from app.recipe_recommendations import Constraints
from validation.track_b import benchmark as tb


def test_scores_treat_a_missed_violation_as_a_false_negative():
    result = tb.scores([(True, True), (True, False), (False, True), (False, False)])
    assert (result["tp"], result["fn"], result["fp"], result["tn"]) == (1, 1, 1, 1)
    assert result["precision"] == result["recall"] == result["f1"] == 0.5


def test_wilson_interval_is_honest_at_the_edges():
    assert tb.wilson(0, 0) is None
    low, high = tb.wilson(10, 10)
    assert high == 1.0 and 0.6 < low < 0.8


def test_gold_labels_are_well_formed():
    gold = tb.load_gold()
    assert len({row["ingredient"] for row in gold}) == len(gold), "duplicate ingredient"
    for row in gold:
        assert {row[c] for c in tb.CONSTRAINTS} <= {"0", "1", "A"}, row
        # Anything non-vegetarian is also non-vegan.
        if row["non_vegetarian"] == "1":
            assert row["non_vegan"] == "1", row


def test_judge_uses_gold_labels_and_leaves_unknown_ingredients_for_review():
    tb.GOLD_LOOKUP.update({rr.normalize_name(r["ingredient"]): r for r in tb.load_gold()})
    recipe = {"ingredients": ["Lard", "Tofu", "Dragon fruit"], "time": 40}
    judged = tb.judge_recipe(recipe, Constraints(diet="Vegetarian", max_minutes=30))
    assert judged["violations"] == ["Lard: non_vegetarian", "time 40 > 30"]
    assert judged["unjudged"] == ["Dragon fruit"]


def fake_recipes(*recipes):
    return json.dumps({"recipes": [
        {"title": title, "ingredients": ingredients, "diet": diet, "minutes": 10, "protein_g": 10,
         "instructions": ["Cook."]} for title, ingredients, diet in recipes]})


def test_generation_ablation_runs_and_restores_production_settings(monkeypatch):
    tb.GOLD_LOOKUP.update({rr.normalize_name(r["ingredient"]): r for r in tb.load_gold()})
    seen = []

    def fake_groq(key, prompt, usage_callback=None, timeout=None):
        seen.append((rr.GROQ_RECIPE_MODEL, rr.RECIPE_PROMPT))
        usage_callback({"input_tokens": 100, "output_tokens": 200})
        # Lard slips past the regex filter, so it is "shown"; chicken is caught by the filter.
        return fake_recipes(("Lard rice", ["Lard", "Rice"], "Vegan"), ("Chicken rice", ["Chicken breast"], "Vegan"),
                            ("Tofu rice", ["Tofu", "Rice"], "Vegan"))

    monkeypatch.setattr(rr, "groq_complete", fake_groq)
    monkeypatch.setattr(tb, "SCENARIOS", tb.SCENARIOS[:1])
    monkeypatch.setattr(tb.time, "sleep", lambda s: None)
    before = (rr.RECIPE_PROMPT, rr.GROQ_RECIPE_MODEL, rr.RECIPE_MODEL)
    runs = tb.experiment_generation({"groq": "fake"}, repeats=2, pause=0)

    assert (rr.RECIPE_PROMPT, rr.GROQ_RECIPE_MODEL, rr.RECIPE_MODEL) == before
    assert {model for model, _ in seen} == {"openai/gpt-oss-120b", "openai/gpt-oss-20b"}
    assert tb.MINIMAL_PROMPT in {prompt for _, prompt in seen}
    gemini = next(r for r in runs if r["model"] == "gemini-3.5-flash-lite")
    assert gemini["status"] == "skipped_missing_key"
    production = runs[0]
    assert production["requests"] == 2 and production["coverage"] == 1.0
    assert production["violation_rate_without_filter"] == pytest.approx(2 / 3, abs=1e-3)
    assert production["violation_rate_shown"] == 0.5  # lard shown, tofu shown, chicken filtered
    assert production["cost_per_1000_requests_usd"] == pytest.approx(0.135)


def test_llm_classifier_scores_llm_and_hybrid(monkeypatch):
    gold = [row for row in tb.load_gold() if row["ingredient"] in {"lard", "chicken breast", "tofu", "coconut milk"}]

    def fake_call(key, model, system, user, usage):
        # Says lard is meat (rules miss it) but forgets chicken breast (rules catch it).
        return json.dumps({"results": [{"ingredient": name, "non_vegetarian": name == "lard", "non_vegan": name == "lard",
                                        "contains_peanut": False} for name in json.loads(user)]})

    monkeypatch.setattr(tb, "CLASSIFIERS", [("groq", "openai/gpt-oss-120b", fake_call)])
    monkeypatch.setattr(tb.time, "sleep", lambda s: None)
    llm, hybrid = tb.experiment_llm_classifier(gold, {"groq": "fake"})
    assert llm["metrics"]["non_vegetarian"]["recall"] == 0.5
    assert hybrid["metrics"]["non_vegetarian"]["recall"] == 1.0


def test_summary_separates_blank_times_and_counts_safe_recipes_the_rules_hid():
    def sample(title, ingredients, violations, shown):
        return {"scenario": "vegan dinner", "status": "ok", "shown": int(shown), "latency_ms": 1.0,
                "estimated_cost_usd": None, "ingredients": {title: ingredients},
                "recipes": [{"title": title, "shown": shown, "violations": violations, "unjudged": []}]}

    summary = tb.summarize_generation([
        sample("Oat porridge", ["Oats", "Almond milk"], [], False),        # compliant, hidden by `milk`
        sample("Rice bowl", ["Rice"], ["time None > 20"], False),          # blank time: hidden, not unsafe
        sample("Bacon rice", ["Bacon", "Rice"], ["Bacon: non_vegan"], False),
    ])
    assert summary["violating_recipes_without_filter"] == 1
    assert summary["time_unknown_recipes"] == 1
    assert summary["wrongly_hidden"] == [{"scenario": "vegan dinner", "title": "Oat porridge", "tripped_by": ["Almond milk"]}]


def test_fisher_exact_matches_known_values():
    # Fisher's tea-tasting table (3/4 vs 1/4): two-sided p = 34/70.
    assert tb.fisher_exact(3, 4, 1, 4) == pytest.approx(34 / 70)
    assert tb.fisher_exact(5, 5, 5, 5) == pytest.approx(1.0)
