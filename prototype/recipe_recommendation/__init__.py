"""Pantry-checked recipe recommendations. The Gemini client is optional."""

from recipe_recommendation.pipeline import (
    Constraints,
    RecommendationResult,
    build_prompt,
    parse_model_output,
    rank_recipes,
    recommend_recipes,
)
from recipe_recommendation.schema import RECIPE_MODEL, RECIPE_PROMPT, RECIPE_SCHEMA

__all__ = [
    "Constraints",
    "RECIPE_MODEL",
    "RECIPE_PROMPT",
    "RECIPE_SCHEMA",
    "RecommendationResult",
    "build_prompt",
    "parse_model_output",
    "rank_recipes",
    "recommend_recipes",
]
