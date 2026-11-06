"""Reproducible offline checks and opt-in live recipe benchmark.

Run from the project root: python -m validation.recommendations.evaluate
Live mode sends only synthetic test pantries, never the saved user database.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from app.recipe_recommendations import (
    GROQ_RECIPE_MODEL, RECIPE_MODEL, Constraints, build_prompt,
    gemini_complete, groq_complete, parse_model_output, rank_recipes,
)
from validation.recommendations.cases import CASES


def check_case(case):
    parsed = parse_model_output(json.dumps({"recipes": case["recipes"]}))
    cards = rank_recipes(parsed.candidates, Constraints(**case["constraints"]), case["pantry"]) if parsed.ok else []
    actual = {"titles": [card["recipe"]["title"] for card in cards], "parse_ok": parsed.ok}
    expected = {"titles": case["expected"], "parse_ok": case.get("parse_ok", True)}
    for field, card_key in (("statuses", "status"), ("scores", "score")):
        if field in case:
            actual[field] = [card[card_key] for card in cards]
            expected[field] = case[field]
    return {"name": case["name"], "known_gap": case.get("known_gap", False),
            "passed": actual == expected, "expected": expected, "actual": actual}


def percentiles(samples):
    ordered = sorted(samples)
    if not ordered:
        return None
    return {"p50_ms": round(statistics.median(ordered), 4),
            "p95_ms": round(ordered[math.ceil(.95 * len(ordered)) - 1], 4)}


def offline(repeats):
    # Warm imports and one execution of each case before timing.
    rows = [check_case(case) for case in CASES]
    times = []
    for _ in range(repeats):
        for case in CASES:
            start = time.perf_counter()
            check_case(case)
            times.append((time.perf_counter() - start) * 1000)
    return {"kind": "synthetic application checks; not model accuracy",
            "cases": len(rows), "passed": sum(row["passed"] for row in rows),
            "latency_scope": "warm JSON parsing, filtering, ranking and assertion; no network, UI or OCR",
            "timed_executions": len(times), "latency": percentiles(times), "results": rows}


LIVE_CASES = [
    ("vegan pantry dinner", ["Rice", "Chickpeas", "Spinach", "Garlic"], Constraints(diet="Vegan", max_minutes=20)),
    ("vegetarian quick meal", ["Pasta", "Tomatoes", "Cheese"], Constraints(diet="Vegetarian", max_minutes=15)),
    ("avoid peanuts", ["Rice", "Tofu", "Broccoli"], Constraints(diet="Vegan", avoid=["peanut", "groundnut"], max_minutes=30)),
    ("sparse pantry", ["Rice"], Constraints(max_minutes=20)),
    ("protein preference", ["Lentils", "Eggs", "Spinach"], Constraints(diet="Vegetarian", high_protein=True)),
    ("conflicting request", ["Rice", "Spinach"], Constraints(diet="Vegan", request="I want chicken with butter")),
]

# Standard uncached list prices checked 2026-11-04. Output includes billed reasoning.
RATES = {"openai/gpt-oss-120b": (.15, .60), "openai/gpt-oss-20b": (.075, .30),
         "gemini-3.5-flash-lite": (.30, 2.50)}


def live(repeats):
    output = []
    providers = [("Groq", GROQ_RECIPE_MODEL, "GROQ_API_KEY", groq_complete),
                 ("Gemini", RECIPE_MODEL, "GEMINI_API_KEY", gemini_complete)]
    for provider, model, key_name, complete in providers:
        key = os.getenv(key_name, "").strip()
        if not key:
            output.append({"provider": provider, "model": model, "status": "skipped_missing_key", "requests": 0})
            continue
        samples = []
        for name, ingredients, constraints in LIVE_CASES:
            pantry = [{"Ingredient": item, "Quantity": 1, "Unit": "count"} for item in ingredients]
            for repetition in range(repeats):
                usage = {}
                sample = {"case": name, "repetition": repetition + 1}
                start = time.perf_counter()
                try:
                    raw = complete(key, build_prompt(pantry, constraints), usage_callback=usage.update)
                    sample["request_ms"] = round((time.perf_counter() - start) * 1000, 2)
                    parsed = parse_model_output(raw)
                    cards = rank_recipes(parsed.candidates, constraints, pantry) if parsed.ok else []
                    sample.update(status="ok" if parsed.ok else "invalid_output",
                                  returned=len(parsed.candidates), retained=len(cards),
                                  shown=min(3, len(cards)), recipes=parsed.candidates,
                                  human_review="pending")
                except Exception as exc:
                    sample.update(status="error", error_type=type(exc).__name__,
                                  request_ms=round((time.perf_counter() - start) * 1000, 2))
                sample["usage"] = usage or None
                rate = RATES.get(model)
                sample["estimated_list_cost_usd"] = (
                    round((usage["input_tokens"] * rate[0] + usage["output_tokens"] * rate[1]) / 1_000_000, 8)
                    if usage and rate else None)
                samples.append(sample)
        output.append({"provider": provider, "model": model, "status": "measured",
                       "requests": len(samples), "successful": sum(s["status"] == "ok" for s in samples),
                       "latency_all_attempts": percentiles([s["request_ms"] for s in samples]),
                       "latency_successful": percentiles([s["request_ms"] for s in samples if s["status"] == "ok"]),
                       "samples": samples})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Make billable API calls using synthetic pantries")
    parser.add_argument("--repeats", type=int, default=100, help="Offline timing repetitions per case")
    parser.add_argument("--live-repeats", type=int, default=1, help="Requests per live case and provider")
    parser.add_argument("--output", type=Path, default=Path("validation/recommendations/results.json"))
    args = parser.parse_args()
    if args.repeats < 1 or args.live_repeats < 1:
        parser.error("repeat counts must be positive")
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "platform": platform.platform(),
              "offline": offline(args.repeats),
              "live": live(args.live_repeats) if args.live else {"status": "not_requested"}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "cases": report["offline"]["cases"],
                      "passed": report["offline"]["passed"], "latency": report["offline"]["latency"],
                      "live": [{k: row[k] for k in ("provider", "status", "requests")} for row in report["live"]]
                      if isinstance(report["live"], list) else report["live"]}, indent=2))


if __name__ == "__main__":
    main()
