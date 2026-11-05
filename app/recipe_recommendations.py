"""Groq-first recipe suggestions with Gemini fallback and local pantry ranking."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).resolve().parent / ".env")

# Fast Flash-Lite model. Receipt extraction keeps its own GEMINI_MODEL.
RECIPE_MODEL = "gemini-3.5-flash-lite"
GROQ_RECIPE_MODEL = os.getenv("GROQ_RECIPE_MODEL", "openai/gpt-oss-120b")
THINKING_LEVEL = "low"

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


class Substitution(BaseModel):
    ingredient: str
    instead: str


class RecipeSuggestion(BaseModel):
    title: str | None = None
    minutes: int | None = None
    protein_g: int | None = None
    diet: str | None = None
    cuisine: str | None = None
    emoji: str | None = None
    tags: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    substitutions: list[Substitution] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class RecipeList(BaseModel):
    recipes: list[RecipeSuggestion]


MODEL_SETTINGS = {
    "model": RECIPE_MODEL,
    "response_mime_type": "application/json",
    "response_schema": "RecipeList",
    "thinking_level": THINKING_LEVEL,
    "temperature": "omitted; Gemini 3 defaults",
}

_MEAT_RE = re.compile(
    r"\b(chicken|beef|pork|lamb|fish|salmon|tuna|shrimp|prawn|turkey|bacon|ham|gelatin|anchovy|steak|meat|seafood|cod)\b",
    re.I,
)
_ANIMAL_RE = re.compile(
    r"\b(egg|eggs|milk|cheese|yogurt|yoghurt|butter|honey|cream|ghee|paneer|whey)\b",
    re.I,
)
_DIET_ALIASES = {
    "vegan": "Vegan",
    "plant-based": "Vegan",
    "plant based": "Vegan",
    "vegetarian": "Vegetarian",
    "veggie": "Vegetarian",
    "omnivore": "Omnivore",
    "none": "Omnivore",
    "no restriction": "Omnivore",
}
_MARKABLE = ("title", "minutes", "protein_g", "diet", "ingredients", "instructions")


@dataclass
class Constraints:
    diet: str = "No preference"
    max_minutes: int | None = None
    avoid: list[str] = field(default_factory=list)
    cuisine: str = "Any"
    priority: str = "Best pantry match"
    high_protein: bool = False
    request: str = ""


@dataclass
class RecommendationResult:
    ok: bool
    error: str | None
    candidates: list[dict] = field(default_factory=list)
    notice: str | None = None


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip()).lower()


def build_prompt(pantry: list[dict], constraints: Constraints) -> str:
    """Prompt text. The API key is never included."""
    lines = [RECIPE_PROMPT, "", "Confirmed pantry:"]
    for item in pantry:
        name = str(item.get("Ingredient", "")).strip()
        if not name:
            continue
        qty = item.get("Quantity", "")
        unit = str(item.get("Unit", "")).strip()
        lines.append(f"- {name}: {qty} {unit}".rstrip())
    lines.append("")
    lines.append(f"Diet hard filter: {constraints.diet}")
    if constraints.max_minutes is None:
        lines.append("Maximum minutes: none")
    else:
        lines.append(f"Maximum minutes: {constraints.max_minutes}")
    avoid = [term.strip() for term in constraints.avoid if str(term).strip()]
    lines.append("Avoid ingredients: " + (", ".join(avoid) if avoid else "none"))
    lines.append(f"Cuisine preference (not a hard filter): {constraints.cuisine}")
    lines.append(f"Ranking priority: {constraints.priority}")
    lines.append(f"Prefer high protein: {'yes' if constraints.high_protein else 'no'}")
    request = constraints.request.strip()
    lines.append("Meal request: " + (request if request else "none"))
    return "\n".join(lines)


def recommend_recipes(
    pantry: list[dict],
    constraints: Constraints,
    api_key: str | None = None,
    complete=None,
    groq_api_key: str | None = None,
) -> RecommendationResult:
    """Try configured providers in order, including fallback on invalid output."""
    items = [row for row in pantry if str(row.get("Ingredient", "")).strip()]
    if not items:
        return RecommendationResult(
            False,
            "Add at least one confirmed pantry item before ranking. No recipes were invented.",
            [],
        )
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    groq_key = (groq_api_key or os.getenv("GROQ_API_KEY") or "").strip()
    if not key and not groq_key:
        return RecommendationResult(
            False,
            "Add a Groq or Gemini API key on the receipt tab, or set GROQ_API_KEY or GEMINI_API_KEY. Nothing was sent.",
            [],
        )
    prompt = build_prompt(items, constraints)
    providers = []
    if groq_key:
        providers.append(("Groq", GROQ_RECIPE_MODEL, lambda text: groq_complete(groq_key, text)))
    if key:
        providers.append(("Gemini", RECIPE_MODEL, lambda text: gemini_complete(key, text)))
    if complete is not None:
        name, model, _ = providers[0]
        providers = [(name, model, complete)]
    errors = []
    for name, model, caller in providers:
        try:
            parsed = parse_model_output(caller(prompt))
            if not parsed.ok:
                errors.append(f"{name}: {parsed.error}")
                continue
        except Exception as exc:  # noqa: BLE001
            detail = _public_error(exc, secrets=(key, groq_key))
            errors.append(f"{name}: {detail}")
            continue
        for recipe in parsed.candidates:
            recipe["source"] = f"{name} {model}"
        if errors:
            parsed.notice = f"Groq was unavailable or returned invalid output. Used {name} instead."
        return parsed
    return _failure(f"Recipe ranking failed ({'; '.join(errors)}). No recipes were shown.")


def groq_complete(api_key: str, prompt: str, client_factory=None, usage_callback=None) -> str:
    """Request JSON, with the same recipe schema and checks as Gemini."""
    if client_factory is None:
        from groq import Groq

        client_factory = Groq
    client = client_factory(api_key=api_key, timeout=20.0, max_retries=0)
    try:
        response = client.chat.completions.create(
            model=GROQ_RECIPE_MODEL,
            messages=[
                {"role": "system", "content": "Return only JSON matching this schema: " + json.dumps(RecipeList.model_json_schema())},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=3000,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        usage = getattr(response, "usage", None)
        if usage_callback and usage:
            usage_callback({"input_tokens": usage.prompt_tokens, "output_tokens": usage.completion_tokens})
        if not content:
            raise RuntimeError("Groq returned an empty response.")
        return content
    finally:
        client.close()


def gemini_complete(api_key: str, prompt: str, client_factory=None, config_builder=None, usage_callback=None) -> str:
    """One generateContent call through the receipt extractor's Gemini client."""
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("Gemini API key was not provided. Enter a Gemini API key in the application.")
    if client_factory is None:
        from app.receipt_extractor import get_gemini_client

        client_factory = get_gemini_client
    client = client_factory(key)
    try:
        if config_builder is None:
            from google.genai import types

            settings = {
                "response_mime_type": "application/json",
                "response_schema": RecipeList,
            }
            thinking = getattr(types, "ThinkingConfig", None)
            if thinking is not None:
                settings["thinking_config"] = thinking(thinking_level=THINKING_LEVEL)
            config = types.GenerateContentConfig(**settings)
        else:
            config = config_builder()
        response = client.models.generate_content(
            model=RECIPE_MODEL,
            contents=prompt,
            config=config,
        )
        usage = getattr(response, "usage_metadata", None)
        if usage_callback and usage:
            usage_callback({
                "input_tokens": usage.prompt_token_count or 0,
                "output_tokens": (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0),
            })
    finally:
        close = getattr(client, "close", None)
        if close:
            close()
    parsed = getattr(response, "parsed", None)
    if parsed is not None:
        if hasattr(parsed, "model_dump_json"):
            return parsed.model_dump_json()
        return json.dumps(parsed)
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text


def parse_model_output(raw: str) -> RecommendationResult:
    """Invalid JSON or inconsistent ingredients yield zero recipes."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _failure("The model did not return valid JSON. No recipes were shown.")
    if not isinstance(payload, dict) or not isinstance(payload.get("recipes"), list):
        return _failure("The model response did not contain a recipe list. No recipes were shown.")

    recipes: list[dict] = []
    for index, entry in enumerate(payload["recipes"], start=1):
        if not isinstance(entry, dict):
            return _failure("A recipe was not an object. No recipes were shown.")
        checked = _recipe_from_entry(entry, index)
        if isinstance(checked, str):
            return _failure(checked)
        recipes.append(checked)
    return RecommendationResult(True, None, recipes)


def rank_recipes(recipes: list[dict], constraints: Constraints, pantry: list[dict]) -> list[dict]:
    """Drop hard-filter misses, then order the rest by pantry overlap."""
    available = {normalize_name(row.get("Ingredient", "")) for row in pantry}
    available.discard("")
    cards = []
    for recipe in recipes:
        if not _passes_hard_filters(recipe, constraints):
            continue
        cards.append(_card(recipe, available, constraints))
    cards.sort(key=lambda card: _sort_key(card, constraints))
    return cards


def _recipe_from_entry(entry: dict, index: int) -> dict | str:
    ingredients = entry.get("ingredients")
    if ingredients is None:
        ingredients = []
    if not isinstance(ingredients, list) or not all(isinstance(item, str) for item in ingredients):
        return "The model returned inconsistent ingredients. No recipes were shown."
    cleaned = [item.strip() for item in ingredients]
    if any(not item for item in cleaned):
        return "The model returned inconsistent ingredients. No recipes were shown."
    normalized = [normalize_name(item) for item in cleaned]
    if len(normalized) != len(set(normalized)):
        return "The model returned inconsistent ingredients. No recipes were shown."

    substitutions_raw = entry.get("substitutions") or []
    if not isinstance(substitutions_raw, list):
        return "The model returned inconsistent ingredients. No recipes were shown."
    substitutions: dict[str, str] = {}
    known = set(normalized)
    for sub in substitutions_raw:
        if not isinstance(sub, dict):
            return "The model returned inconsistent ingredients. No recipes were shown."
        ingredient = str(sub.get("ingredient", "")).strip()
        instead = str(sub.get("instead", "")).strip()
        if not ingredient or normalize_name(ingredient) not in known:
            return "The model returned inconsistent ingredients. No recipes were shown."
        substitutions[ingredient] = instead or "another ingredient you choose"

    instructions = entry.get("instructions")
    if instructions is None:
        instructions = []
    if not isinstance(instructions, list) or not all(isinstance(step, str) and step.strip() for step in instructions):
        if instructions not in ([], None):
            return "The model returned inconsistent ingredients. No recipes were shown."
        instructions = []

    declared = entry.get("missing_fields") or []
    if not isinstance(declared, list):
        declared = []
    missing = [name for name in declared if name in _MARKABLE]
    title = entry.get("title")
    title = title.strip() if isinstance(title, str) else ""
    if not title and "title" not in missing:
        missing.append("title")
    minutes = _whole_number(entry.get("minutes"))
    if minutes is None and "minutes" not in missing:
        missing.append("minutes")
    protein = _whole_number(entry.get("protein_g"))
    if protein is None and "protein_g" not in missing:
        missing.append("protein_g")
    diet = _diet_label(entry.get("diet"))
    if diet is None and "diet" not in missing:
        missing.append("diet")
    if not cleaned and "ingredients" not in missing:
        missing.append("ingredients")
    if not instructions and "instructions" not in missing:
        missing.append("instructions")

    tags = entry.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    cuisine = entry.get("cuisine")
    cuisine = cuisine.strip() if isinstance(cuisine, str) and cuisine.strip() else None
    emoji = entry.get("emoji")
    emoji = emoji.strip() if isinstance(emoji, str) and emoji.strip() else "🍽️"
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "recipe").lower()).strip("-") or "recipe"
    return {
        "id": f"{slug}-{index}",
        "title": title or "Untitled recipe",
        "time": minutes,
        "protein": protein,
        "diet": diet,
        "cuisine": cuisine,
        "emoji": emoji,
        "tags": [str(tag) for tag in tags if str(tag).strip()],
        "ingredients": cleaned,
        "instructions": [step.strip() for step in instructions],
        "substitutions": substitutions,
        "missing_fields": missing,
        "source": "AI suggestion",
    }


def _passes_hard_filters(recipe: dict, constraints: Constraints) -> bool:
    diet = constraints.diet
    label = recipe.get("diet")
    if diet == "Vegan" and label != "Vegan":
        return False
    if diet == "Vegetarian" and label not in {"Vegetarian", "Vegan"}:
        return False
    if diet in {"Vegan", "Vegetarian"} and _ingredients_break_diet(recipe.get("ingredients") or [], diet):
        return False
    if constraints.max_minutes is not None:
        minutes = recipe.get("time")
        if minutes is None or minutes > constraints.max_minutes:
            return False
    avoid = [normalize_name(term) for term in constraints.avoid if str(term).strip()]
    if avoid and any(_hits_avoid(ingredient, avoid) for ingredient in recipe.get("ingredients") or []):
        return False
    return True


def _ingredients_break_diet(ingredients: list[str], diet: str) -> bool:
    for ingredient in ingredients:
        if _MEAT_RE.search(ingredient):
            return True
        if diet == "Vegan" and _ANIMAL_RE.search(ingredient):
            return True
    return False


def _hits_avoid(ingredient: str, avoid: list[str]) -> bool:
    name = normalize_name(ingredient)
    return any(term and (term in name or name in term) for term in avoid)


def _card(recipe: dict, available: set[str], constraints: Constraints) -> dict:
    ingredients = list(recipe.get("ingredients") or [])
    missing = [item for item in ingredients if normalize_name(item) not in available]
    if not ingredients:
        missing_note = "Ingredients were not returned"
    else:
        missing_note = None
    required = len(ingredients)
    have = required - len(missing)
    score = round(100 * have / required) if required else 0
    if not ingredients or len(missing) >= 3:
        status, status_class = "Needs shopping", "status-shop"
    elif not missing:
        status, status_class = "Cook now", "status-cook"
    else:
        status, status_class = "Almost ready", "status-almost"

    if not ingredients:
        reason = "Ingredients were not returned, so this cannot be matched to the pantry."
    elif not missing:
        reason = "All listed ingredients are in the confirmed pantry."
    else:
        reason = f"{have}/{required} listed ingredients are in the confirmed pantry."
    if constraints.cuisine not in {"", "Any"} and recipe.get("cuisine") == constraints.cuisine:
        reason = reason[:-1] + f", and the cuisine matches {constraints.cuisine}."
    field_notes = [_field_note(name) for name in recipe.get("missing_fields") or []]
    return {
        "recipe": recipe,
        "score": score,
        "missing": missing if ingredients else [missing_note],
        "available_count": have,
        "required_count": required,
        "status": status,
        "status_class": status_class,
        "reason": reason,
        "field_notes": [note for note in field_notes if note],
    }


def _field_note(name: str) -> str:
    labels = {
        "title": "Title was not returned.",
        "minutes": "Cooking time was not returned.",
        "protein_g": "Protein was not returned.",
        "diet": "Diet was not returned.",
        "ingredients": "Ingredients were not returned.",
        "instructions": "Steps were not returned.",
    }
    return labels.get(name, "")


def _sort_key(card: dict, constraints: Constraints) -> tuple:
    recipe = card["recipe"]
    score = card["score"]
    missing_n = len(card["missing"])
    minutes = recipe["time"] if isinstance(recipe.get("time"), int) else 10**6
    protein = recipe["protein"] if isinstance(recipe.get("protein"), int) else -1
    priority = constraints.priority
    if priority == "Fastest":
        return (minutes, -score, missing_n)
    if priority == "Highest protein":
        return (-protein, -score, missing_n)
    if priority == "Fewest missing ingredients":
        return (missing_n, -score, minutes)
    if constraints.high_protein:
        return (-score, missing_n, -protein, minutes)
    return (-score, missing_n, minutes)


def _diet_label(value) -> str | None:
    if not isinstance(value, str):
        return None
    return _DIET_ALIASES.get(value.strip().lower())


def _whole_number(value) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and value.is_integer():
        return int(value) if value >= 0 else None
    return None


def _failure(message: str) -> RecommendationResult:
    return RecommendationResult(False, message, [])


def _public_error(exc: Exception, secrets=()) -> str:
    name = exc.__class__.__name__
    text = " ".join(str(exc).split())
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[redacted]")
    text = re.sub(r"(?i)([?&]key=)[^&\s\"']+", r"\1[redacted]", text)
    text = re.sub(r"AIza[0-9A-Za-z_\-]{10,}", "[redacted]", text)
    text = re.sub(r"gsk_[0-9A-Za-z_\-]+", "[redacted]", text)
    if not text or text == name:
        return name
    if len(text) > 240:
        text = text[:239].rstrip() + "…"
    return f"{name}: {text}"
