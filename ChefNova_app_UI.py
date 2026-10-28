import html
import io
import os
import re
import tempfile
from pathlib import Path
from copy import deepcopy

import pandas as pd
import streamlit as st

from app.receipt_extractor import extract_receipt
from app.recipe_recommendations import RECIPE_MODEL, Constraints, rank_recipes, recommend_recipes

try:
    import speech_recognition as sr
except ImportError:
    sr = None


st.set_page_config(page_title="ChefNova", page_icon="🍳", layout="wide")

# ---------- Visual system ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: Inter, sans-serif; }
.stApp {
    background: linear-gradient(rgba(248,246,241,.91),rgba(248,246,241,.95)),
                url("https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=2200&q=85");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #202020;
}
[data-testid="stSidebar"] {
    background: rgba(255,255,255,.94);
    border-right: 1px solid #e3ded5;
    backdrop-filter: blur(12px);
}
[data-testid="stHeader"] { background: rgba(248,246,241,.75); }
[data-testid="stAppViewContainer"] { background: transparent; }
[data-testid="stMainBlockContainer"] { padding-top: 2.5rem; }
[data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }

.brand { padding: 0 8px 24px; }
.brand-title { font-size: 25px; font-weight: 700; color: #171717; }
.brand-sub { font-size: 12px; color: #777; margin-top: 3px; }

.page-title { font-size: 31px; font-weight: 700; color: #171717; margin-bottom: 3px; letter-spacing: -.02em; }
.hero-accent { display: inline-block; width: 42px; height: 4px; border-radius: 20px; background: #c9794b; margin-bottom: 12px; }
.page-subtitle { color: #777; font-size: 14px; margin-bottom: 22px; }
.section-title { font-size: 19px; font-weight: 650; color: #202020; margin: 5px 0 13px; }

.card, .chat-card {
    background: rgba(255,255,255,.94);
    border: 1px solid rgba(224,219,209,.95);
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 8px 30px rgba(74,62,45,.07);
    backdrop-filter: blur(7px);
}

.recipe-card {
    background: rgba(255,255,255,.96);
    border: 1px solid rgba(224,219,209,.95);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 8px 28px rgba(74,62,45,.08);
    transition: transform .18s ease, box-shadow .18s ease;
}
.recipe-card:hover { transform: translateY(-3px); box-shadow: 0 12px 32px rgba(74,62,45,.12); }
.recipe-image {
    height: 118px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg,#eee8dc,#d8c6ab);
    font-size: 48px;
}
.recipe-body { padding: 16px; }
.recipe-name { font-size: 17px; font-weight: 650; color: #202020; }
.recipe-meta { font-size: 12px; color: #777; margin: 6px 0 10px; }
.recipe-reason { font-size: 12px; color: #666; line-height: 1.45; margin-top: 8px; min-height: 50px; }
.score-badge {
    display: inline-block;
    padding: 5px 9px;
    border-radius: 999px;
    background: #f7e9df;
    color: #8d4d2d;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 8px;
}

.pill {
    display: inline-block;
    background: #f0efe9;
    color: #555;
    padding: 6px 10px;
    border-radius: 20px;
    margin: 0 5px 7px 0;
    font-size: 11px;
}
.small-note { font-size: 12px; color: #7c7c77; line-height: 1.55; }
.available {
    background: #f2f7f1;
    border: 1px solid #d5e3d1;
    color: #41613b;
    border-radius: 10px;
    padding: 11px;
    font-size: 13px;
    margin-bottom: 8px;
}
.missing {
    background: #fff5f0;
    border: 1px solid #efd4c7;
    color: #8a4a34;
    border-radius: 10px;
    padding: 11px;
    font-size: 13px;
    margin-bottom: 8px;
}
.status-cook {
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:#eef7eb; color:#41613b; font-size:11px; font-weight:700;
}
.status-almost {
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:#fff7e8; color:#8a6422; font-size:11px; font-weight:700;
}
.status-shop {
    display:inline-block; padding:6px 10px; border-radius:999px;
    background:#fff0eb; color:#8a4a34; font-size:11px; font-weight:700;
}

/* Compact microphone control */
[data-testid="stAudioInput"] {
    width: 52px !important;
    min-width: 52px !important;
    overflow: hidden !important;
    margin: 0 !important;
}
[data-testid="stAudioInput"] > div {
    width: 52px !important;
    min-width: 52px !important;
    overflow: hidden !important;
}

div.stButton > button {
    border-radius: 10px;
    min-height: 42px;
    font-weight: 600;
    border: 1px solid #c9794b;
    background: #c9794b;
    color: white;
    transition: all .15s ease;
}
div.stButton > button:hover {
    background: #ae6239;
    border-color: #ae6239;
    color: white;
}

/* The page is light. Tab labels and typed fields were inheriting white theme text. */
[data-testid="stTabs"] button,
[data-testid="stTabs"] [data-baseweb="tab"],
[data-testid="stTabs"] [data-baseweb="tab"] p {
    color: #3a342c !important;
}
[data-testid="stTabs"] button[aria-selected="true"],
[data-testid="stTabs"] [aria-selected="true"],
[data-testid="stTabs"] [aria-selected="true"] p {
    color: #171717 !important;
}
[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea,
[data-baseweb="input"] input {
    color: #171717 !important;
    -webkit-text-fill-color: #171717 !important;
    background-color: #fffdf9 !important;
    caret-color: #171717 !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-baseweb="input"] input::placeholder {
    color: #6f6a62 !important;
    -webkit-text-fill-color: #6f6a62 !important;
    opacity: 1 !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextInput"] label p,
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p {
    color: #202020 !important;
}
.pill-row { display:flex; align-items:center; gap:4px; flex-wrap:wrap; margin-top:8px; }
.pill-row .pill { margin:0; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------- Demo data ----------
DEFAULT_INVENTORY = [
    {"Ingredient": "Rice", "Quantity": 2, "Unit": "cups"},
    {"Ingredient": "Chickpeas", "Quantity": 2, "Unit": "cans"},
    {"Ingredient": "Spinach", "Quantity": 1, "Unit": "bag"},
    {"Ingredient": "Tomatoes", "Quantity": 4, "Unit": "count"},
    {"Ingredient": "Greek Yogurt", "Quantity": 1, "Unit": "container"},
    {"Ingredient": "Garlic", "Quantity": 1, "Unit": "bulb"},
]

# Original demo recipes. Ranking does not read this list; Gemini proposes the recipes.
RECIPE_DB = [
    {
        "id": "spinach_chickpea_bowl",
        "title": "Spinach Chickpea Rice Bowl",
        "emoji": "🥗",
        "time": 18,
        "protein": 24,
        "diet": "Vegetarian",
        "cuisine": "Mediterranean",
        "tags": ["High protein", "Pantry-friendly"],
        "ingredients": ["Rice", "Chickpeas", "Spinach", "Tomatoes", "Garlic", "Greek Yogurt"],
        "instructions": [
            "Sauté chopped garlic and tomatoes for 3–4 minutes.",
            "Add chickpeas, salt, pepper, and your preferred seasoning.",
            "Fold in spinach until just wilted.",
            "Serve over warm rice and finish with Greek yogurt.",
        ],
        "substitutions": {"Spinach": "kale or another leafy green", "Greek Yogurt": "plain yogurt or a dairy-free yogurt"},
        "source": "ChefNova curated demo recipe dataset",
    },
    {
        "id": "creamy_chickpea_curry",
        "title": "Creamy Spinach Chickpea Curry",
        "emoji": "🍛",
        "time": 20,
        "protein": 22,
        "diet": "Vegetarian",
        "cuisine": "Indian",
        "tags": ["High protein", "One pot"],
        "ingredients": ["Chickpeas", "Spinach", "Tomatoes", "Garlic", "Greek Yogurt", "Rice"],
        "instructions": [
            "Cook garlic and tomatoes until softened.",
            "Add chickpeas and curry spices, then simmer briefly.",
            "Stir in spinach until wilted.",
            "Remove from high heat, fold in yogurt, and serve with rice.",
        ],
        "substitutions": {"Spinach": "kale", "Greek Yogurt": "coconut yogurt"},
        "source": "ChefNova curated demo recipe dataset",
    },
    {
        "id": "garlic_tomato_chickpea_rice",
        "title": "Garlic Tomato Chickpea Rice",
        "emoji": "🍚",
        "time": 17,
        "protein": 18,
        "diet": "Vegan",
        "cuisine": "Mediterranean",
        "tags": ["Quick", "Vegan"],
        "ingredients": ["Rice", "Chickpeas", "Tomatoes", "Garlic"],
        "instructions": [
            "Sauté garlic in a lightly oiled pan.",
            "Add tomatoes and cook until they break down slightly.",
            "Stir in chickpeas and cooked rice.",
            "Season and cook for another 2–3 minutes before serving.",
        ],
        "substitutions": {},
        "source": "ChefNova curated demo recipe dataset",
    },
    {
        "id": "yogurt_chickpea_bowl",
        "title": "Garlic Yogurt Chickpea Bowl",
        "emoji": "🥣",
        "time": 12,
        "protein": 21,
        "diet": "Vegetarian",
        "cuisine": "Mediterranean",
        "tags": ["Fast", "High protein"],
        "ingredients": ["Chickpeas", "Greek Yogurt", "Tomatoes", "Garlic"],
        "instructions": [
            "Mix Greek yogurt with finely chopped garlic, salt, and pepper.",
            "Warm chickpeas and chopped tomatoes in a pan.",
            "Spoon the yogurt sauce into a bowl and add the warm chickpeas.",
            "Finish with herbs or chili flakes if available.",
        ],
        "substitutions": {"Greek Yogurt": "plain yogurt or dairy-free yogurt"},
        "source": "ChefNova curated demo recipe dataset",
    },
    {
        "id": "tomato_garlic_rice",
        "title": "Tomato Garlic Rice",
        "emoji": "🍅",
        "time": 12,
        "protein": 8,
        "diet": "Vegan",
        "cuisine": "Asian",
        "tags": ["Very fast", "Few ingredients"],
        "ingredients": ["Rice", "Tomatoes", "Garlic"],
        "instructions": [
            "Sauté garlic until fragrant.",
            "Add chopped tomatoes and cook until softened.",
            "Add cooked rice and toss until evenly coated.",
            "Season to taste and serve hot.",
        ],
        "substitutions": {},
        "source": "ChefNova curated demo recipe dataset",
    },
    {
        "id": "spicy_chickpea_rice",
        "title": "Spicy Chickpea Tomato Rice",
        "emoji": "🌶️",
        "time": 16,
        "protein": 19,
        "diet": "Vegan",
        "cuisine": "Indian",
        "tags": ["Spicy", "Quick"],
        "ingredients": ["Rice", "Chickpeas", "Tomatoes", "Garlic"],
        "instructions": [
            "Sauté garlic with chili flakes or chili powder.",
            "Add tomatoes and cook into a quick sauce.",
            "Add chickpeas and rice, then toss well.",
            "Adjust spice level and serve immediately.",
        ],
        "substitutions": {},
        "source": "ChefNova curated demo recipe dataset",
    },
    {
        "id": "chickpea_spinach_salad",
        "title": "Chickpea Spinach Tomato Salad",
        "emoji": "🥬",
        "time": 10,
        "protein": 17,
        "diet": "Vegan",
        "cuisine": "Mediterranean",
        "tags": ["No-cook", "Fresh"],
        "ingredients": ["Chickpeas", "Spinach", "Tomatoes"],
        "instructions": [
            "Rinse and drain chickpeas.",
            "Combine chickpeas, spinach, and chopped tomatoes.",
            "Season with salt, pepper, and any preferred dressing.",
            "Toss and serve immediately.",
        ],
        "substitutions": {"Spinach": "mixed greens or kale"},
        "source": "ChefNova curated demo recipe dataset",
    },
    {
        "id": "creamy_tomato_rice",
        "title": "Creamy Tomato Yogurt Rice",
        "emoji": "🍲",
        "time": 15,
        "protein": 12,
        "diet": "Vegetarian",
        "cuisine": "Indian",
        "tags": ["Comfort food", "Quick"],
        "ingredients": ["Rice", "Tomatoes", "Greek Yogurt", "Garlic"],
        "instructions": [
            "Cook garlic and tomatoes until soft.",
            "Fold in cooked rice and warm through.",
            "Lower the heat and mix in Greek yogurt.",
            "Season gently and serve warm.",
        ],
        "substitutions": {"Greek Yogurt": "plain yogurt"},
        "source": "ChefNova curated demo recipe dataset",
    },
]


# ---------- Session state ----------
def init_state():
    defaults = {
        "page": "Home",
        "inventory": deepcopy(DEFAULT_INVENTORY),
        "confirmed": False,
        "request": "",
        "review_items": [],
        "messages": [],
        "selected_recipe_id": None,
        "temporary_exclusions": [],
        "conversation_max_time": None,
        "conversation_keywords": [],
        "last_inventory_audio_hash": None,
        "last_refine_audio_hash": None,
        "diet_pref": "Vegetarian",
        "max_time_pref": "20 min",
        "cuisine_pref": "Any",
        "priority_pref": "Best pantry match",
        "high_protein_pref": True,
        "feedback": {},
        "gemini_api_key": "",
        "groq_api_key": "",
        "receipt_extraction_source": None,
        "receipt_ocr_text": None,
        "avoid_pref": "",
        "recommendation_candidates": None,
        "recommendation_error": None,
        "recommendation_notice": None,
        "selected_recipe": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# ---------- Helpers ----------
def normalize_name(name):
    return re.sub(r"\s+", " ", str(name).strip()).lower()


def inventory_names(include_temporary_exclusions=False):
    names = {normalize_name(item["Ingredient"]) for item in st.session_state.inventory if str(item.get("Ingredient", "")).strip()}
    if include_temporary_exclusions:
        names -= {normalize_name(x) for x in st.session_state.temporary_exclusions}
    return names


def clean_number(value, fallback=1):
    try:
        numeric = float(value)
        return int(numeric) if numeric.is_integer() else numeric
    except (TypeError, ValueError):
        return fallback


def merge_inventory_items(items):
    existing = {normalize_name(item["Ingredient"]): item for item in st.session_state.inventory}
    for item in items:
        ingredient = str(item.get("Ingredient", "")).strip()
        if not ingredient:
            continue
        key = normalize_name(ingredient)
        qty = clean_number(item.get("Quantity", 1), 1)
        unit = str(item.get("Unit", "count") or "count").strip()
        if key in existing and normalize_name(existing[key].get("Unit", "")) == normalize_name(unit):
            existing[key]["Quantity"] = clean_number(existing[key].get("Quantity", 0), 0) + qty
        else:
            new_item = {"Ingredient": ingredient.title(), "Quantity": qty, "Unit": unit}
            st.session_state.inventory.append(new_item)
            existing[key] = new_item
    st.session_state.confirmed = False


def parse_grocery_text(text):
    """Simple deterministic parser for prototype manual/voice grocery entry."""
    if not text or not text.strip():
        return []

    number_words = {
        "a": 1,
        "an": 1,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "twelve": 12,
    }
    unit_map = {
        "can": "cans",
        "cans": "cans",
        "bag": "bag",
        "bags": "bags",
        "cup": "cups",
        "cups": "cups",
        "container": "container",
        "containers": "containers",
        "bulb": "bulb",
        "bulbs": "bulbs",
        "lb": "lb",
        "lbs": "lb",
        "pound": "lb",
        "pounds": "lb",
        "gallon": "gallon",
        "gallons": "gallons",
        "oz": "oz",
        "ounce": "oz",
        "ounces": "oz",
        "dozen": "dozen",
        "count": "count",
    }

    text = re.sub(r"\b(i have|i bought|i got|add|we have|we bought)\b", "", text, flags=re.I)
    parts = [p.strip(" .") for p in re.split(r",|\band\b", text, flags=re.I) if p.strip(" .")]
    results = []

    for part in parts:
        part = re.sub(r"^(some|about)\s+", "", part.strip(), flags=re.I)
        tokens = part.split()
        qty = 1
        unit = "count"

        if tokens:
            first = tokens[0].lower()
            if re.fullmatch(r"\d+(?:\.\d+)?", first):
                qty = clean_number(first)
                tokens = tokens[1:]
            elif first in number_words:
                qty = number_words[first]
                tokens = tokens[1:]

        if tokens and tokens[0].lower() in unit_map:
            unit = unit_map[tokens[0].lower()]
            tokens = tokens[1:]
            if tokens and tokens[0].lower() == "of":
                tokens = tokens[1:]

        ingredient = " ".join(tokens).strip()
        if not ingredient:
            continue

        # Sensible default for uncounted food phrases.
        if qty == 1 and unit == "count" and ingredient.lower() in {"rice", "milk", "yogurt"}:
            unit = "item"

        results.append({"Ingredient": ingredient.title(), "Quantity": qty, "Unit": unit})

    return results


def speech_to_text(audio_file):
    if audio_file is None:
        return None, None
    if sr is None:
        return None, "Speech-to-text requires the SpeechRecognition package."
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_file.getvalue())) as source:
            audio_data = recognizer.record(source)
        transcript = recognizer.recognize_google(audio_data)
        return transcript, None
    except Exception as exc:
        return None, f"Voice was captured, but transcription failed: {exc}"


def prototype_receipt_extraction(filename):
    """Deprecated demo extractor kept for backward compatibility."""
    _ = filename
    return []


def validate_receipt_item(item):
    """Deterministic review checks for suspicious receipt extraction values."""
    warnings = []

    quantity = item.get("Quantity")
    unit = str(item.get("Unit") or "").strip().lower()
    package_size = str(item.get("Package Size") or "").strip().lower()
    confidence = item.get("Confidence")

    try:
        quantity_num = float(quantity) if quantity not in (None, "") else None
    except (TypeError, ValueError):
        quantity_num = None
        warnings.append("Quantity could not be interpreted as a number.")

    # Flag implausible weights/sizes rather than silently correcting them.
    weight_units = {"kg", "g", "lb", "lbs", "oz", "ounce", "ounces", "gram", "grams", "kilogram", "kilograms"}
    if unit in weight_units and quantity_num is not None:
        if unit in {"kg", "kilogram", "kilograms"} and quantity_num > 20:
            warnings.append("Unusually large weight; verify the receipt.")
        elif unit in {"g", "gram", "grams"} and quantity_num > 50000:
            warnings.append("Unusually large weight; verify the receipt.")
        elif unit in {"lb", "lbs"} and quantity_num > 100:
            warnings.append("Unusually large weight; verify the receipt.")
        elif unit in {"oz", "ounce", "ounces"} and quantity_num > 5000:
            warnings.append("Unusually large weight; verify the receipt.")

    if package_size:
        if re.search(r"(?:175|250|500)\s*kg", package_size):
            warnings.append("Package size looks implausibly large; verify the receipt.")

    if confidence not in (None, ""):
        try:
            if float(confidence) < 0.80:
                warnings.append("Low extraction confidence; verify this item.")
        except (TypeError, ValueError):
            warnings.append("Confidence value could not be interpreted.")

    return " ".join(warnings)


def build_receipt_review_items(extraction):
    """Convert structured extractor output into the editable review-table format."""
    items = []
    if extraction is None:
        return items

    for item in extraction.items:
        row = {
            "Ingredient": item.name,
            "Quantity": item.quantity,
            "Unit": item.unit or "",
            "Package Size": item.package_size or "",
            "Brand": item.brand or "",
            "Confidence": round(item.confidence, 2),
        }
        row["Review Reason"] = validate_receipt_item(row)
        row["Needs Review"] = bool(row["Review Reason"])
        items.append(row)

    return items


def effective_max_time():
    if st.session_state.conversation_max_time:
        return st.session_state.conversation_max_time
    value = st.session_state.max_time_pref
    if value == "No limit":
        return None
    return int(value.split()[0])


def current_constraints():
    avoid = []
    for part in re.split(r"[,;\n]", st.session_state.avoid_pref or ""):
        term = part.strip()
        if term and term not in avoid:
            avoid.append(term)
    for item in st.session_state.temporary_exclusions:
        if item not in avoid:
            avoid.append(item)
    request = (st.session_state.request or "").strip()
    if st.session_state.conversation_keywords:
        extra = ", ".join(st.session_state.conversation_keywords)
        request = f"{request}\nAlso: {extra}".strip()
    return Constraints(
        diet=st.session_state.diet_pref,
        max_minutes=effective_max_time(),
        avoid=avoid,
        cuisine=st.session_state.cuisine_pref,
        priority=st.session_state.priority_pref,
        high_protein=bool(st.session_state.high_protein_pref),
        request=request,
    )


def refresh_recommendations():
    """Ask Gemini once. An empty pantry or a missing key never leaves this process."""
    result = recommend_recipes(
        st.session_state.inventory,
        current_constraints(),
        api_key=(st.session_state.gemini_api_key or "").strip() or None,
    )
    st.session_state.recommendation_candidates = result.candidates
    st.session_state.recommendation_error = result.error
    st.session_state.recommendation_notice = result.notice
    st.session_state.selected_recipe = None


def visible_recommendations():
    candidates = st.session_state.recommendation_candidates
    if st.session_state.recommendation_error or not candidates:
        return []
    return rank_recipes(candidates, current_constraints(), st.session_state.inventory)


def extract_known_ingredient_from_message(text):
    names = {normalize_name(item["Ingredient"]) for item in st.session_state.inventory}
    for recipe in st.session_state.recommendation_candidates or []:
        names.update(normalize_name(ingredient) for ingredient in recipe.get("ingredients") or [])
    names.discard("")
    lower = text.lower()
    for name in sorted(names, key=len, reverse=True):
        if name in lower:
            return name.title()
    return None


def process_refinement(text):
    text = text.strip()
    if not text:
        return

    st.session_state.messages.append({"role": "user", "text": text})
    lower = text.lower()
    reply = (
        "I re-filtered the recipes Gemini already returned. "
        "Nothing new was invented, and your confirmed pantry was not changed."
    )

    ingredient = extract_known_ingredient_from_message(text)
    negative_patterns = ["don't have", "do not have", "no ", "without ", "don't want", "do not want"]
    if ingredient and any(pattern in lower for pattern in negative_patterns):
        if ingredient not in st.session_state.temporary_exclusions:
            st.session_state.temporary_exclusions.append(ingredient)
        reply = (
            f"I hid recipes that use {ingredient}. "
            "This only filters the current Gemini list. Your confirmed pantry was not changed."
        )
    else:
        minute_match = re.search(r"(\d{1,2})\s*(?:min|minute)", lower)
        if minute_match:
            st.session_state.conversation_max_time = int(minute_match.group(1))
            reply = (
                f"I kept only returned recipes that take {minute_match.group(1)} minutes or less. "
                "Recipes with no listed time are hidden, because they cannot prove the limit."
            )
        elif "spicy" in lower:
            if "spicy" not in st.session_state.conversation_keywords:
                st.session_state.conversation_keywords.append("spicy")
            reply = "I noted spicy for the next Gemini request. The cards on screen are still the recipes already returned."
        elif "quick" in lower or "faster" in lower:
            st.session_state.priority_pref = "Fastest"
            reply = "I reordered the current Gemini recipes with the fastest listed time first."
        elif "protein" in lower:
            st.session_state.high_protein_pref = True
            st.session_state.priority_pref = "Highest protein"
            reply = "I reordered the current Gemini recipes with the highest listed protein first."

    st.session_state.messages.append({"role": "assistant", "text": reply})


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-title">🍳 ChefNova</div>
            <div class="brand-sub">Your AI kitchen companion</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("⌂  Home", use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()
    if st.button("▦  My Inventory", use_container_width=True):
        st.session_state.page = "My Inventory"
        st.rerun()
    if st.button("＋  Get Recipe", use_container_width=True):
        st.session_state.page = "Get Recipe"
        st.rerun()
    if st.button("◎  Evaluation Plan", use_container_width=True):
        st.session_state.page = "Evaluation Plan"
        st.rerun()

    st.markdown("---")
    st.markdown(
        f"""
        <div class="small-note">
        <b>Inventory status</b><br><br>
        {'✓ Confirmed' if st.session_state.confirmed else '! Needs review'}<br>
        {len(st.session_state.inventory)} pantry items<br><br>
        <b>Design principle</b><br><br>
        You control what is actually in your kitchen.<br><br>
        ChefNova interprets, recommends, and adapts.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Home ----------
def show_home():
    st.markdown(
        """
        <div style="padding:30px 36px 26px 36px;border-radius:22px;background:rgba(255,255,255,.80);border:1px solid rgba(226,218,206,.88);box-shadow:0 10px 28px rgba(74,62,45,.06);backdrop-filter:blur(8px);">
            <div class="hero-accent"></div>
            <div style="font-size:12px;color:#8a705f;font-weight:700;letter-spacing:.10em;text-transform:uppercase;">YOUR AI KITCHEN COMPANION</div>
            <div style="font-size:34px;font-weight:700;color:#171717;margin-top:8px;line-height:1.15;">What can we cook with what you have?</div>
            <div style="font-size:14px;color:#777;margin-top:10px;max-width:800px;line-height:1.5;">ChefNova turns your confirmed grocery inventory into ranked meals that fit your diet, preferences, and time.</div>
            <div style="font-size:15px;font-weight:650;color:#333;margin-top:20px;">What are you in the mood for?</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.session_state.request = st.text_area(
        "Home meal request",
        value=st.session_state.request,
        placeholder="e.g. I want a quick vegetarian dinner with lots of protein...",
        height=82,
        label_visibility="collapsed",
    )

    st.markdown(
        """
        <div class="pill-row">
            <span class="pill">Inventory-aware</span>
            <span class="pill">Preference-ranked</span>
            <span class="pill">Conversational</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    if st.button("Find Recipes  →", key="home_find", use_container_width=True):
        if not st.session_state.confirmed:
            st.info("Start by reviewing and confirming your inventory.")
            st.session_state.page = "My Inventory"
        else:
            st.session_state.page = "Get Recipe"
        st.rerun()

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        with st.container(border=True):
            st.markdown(
                """
                <div style="min-height:115px;">
                    <div style="font-size:25px;">🧾</div>
                    <div style="font-size:18px;font-weight:650;margin-top:7px;">Add groceries your way</div>
                    <div class="small-note" style="margin-top:6px;">Upload a receipt, type ingredients, or use your voice. Review everything before it enters the pantry.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Manage Inventory", key="home_receipt", use_container_width=True):
                st.session_state.page = "My Inventory"
                st.rerun()

    with c2:
        status = "Inventory confirmed" if st.session_state.confirmed else "Inventory needs review"
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="min-height:115px;">
                    <div style="font-size:25px;">🥕</div>
                    <div style="font-size:18px;font-weight:650;margin-top:7px;">My Inventory</div>
                    <div class="small-note" style="margin-top:6px;">{status}. ChefNova currently knows about {len(st.session_state.inventory)} pantry items.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("View Inventory  →", key="home_inventory", use_container_width=True):
                st.session_state.page = "My Inventory"
                st.rerun()

    with c3:
        with st.container(border=True):
            st.markdown(
                """
                <div style="min-height:115px;">
                    <div style="font-size:25px;">🎯</div>
                    <div style="font-size:18px;font-weight:650;margin-top:7px;">Explainable ranking</div>
                    <div class="small-note" style="margin-top:6px;">Gemini proposes recipes. Cook now, Almost ready, and Needs shopping come from how many ingredients you already have.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Set Preferences", key="home_preferences", use_container_width=True):
                st.session_state.page = "Get Recipe"
                st.rerun()


# ---------- Inventory ----------
def show_inventory():
    st.markdown('<div class="page-title">My Inventory</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Add groceries by receipt, typing, or voice. Review the result before ChefNova treats it as true pantry data.</div>',
        unsafe_allow_html=True,
    )

    add_tab, pantry_tab = st.tabs(["＋ Add groceries", "🥕 Current pantry"])

    with add_tab:
        left, right = st.columns([1.35, 1], gap="large")

        with left:
            st.markdown('<div class="section-title">1. Choose an input method</div>', unsafe_allow_html=True)
            receipt_tab, type_tab, voice_tab = st.tabs(["🧾 Receipt", "⌨️ Type", "🎙 Voice"])

            with receipt_tab:
                st.markdown("### 🔑 AI API Keys")
                st.caption("Keys are used only for this session and are not written to the repository, database, or logs.")

                key_col1, key_col2 = st.columns(2)
                with key_col1:
                    st.session_state.gemini_api_key = st.text_input(
                        "Gemini API key",
                        value=st.session_state.gemini_api_key,
                        type="password",
                        placeholder="Enter Gemini API key",
                        key="gemini_api_key_input",
                    )
                with key_col2:
                    st.session_state.groq_api_key = st.text_input(
                        "Groq API key",
                        value=st.session_state.groq_api_key,
                        type="password",
                        placeholder="Enter Groq API key",
                        key="groq_api_key_input",
                    )

                receipt = st.file_uploader(
                    "Upload a receipt or grocery-order screenshot",
                    type=["png", "jpg", "jpeg", "webp"],
                    help="ChefNova runs local Tesseract OCR, then Gemini, with Groq as the fallback model.",
                )

                if receipt is not None:
                    st.success(f"Receipt ready: {receipt.name}")

                    if st.button(
                        "Extract grocery items",
                        key="extract_receipt",
                        use_container_width=True,
                        disabled=not st.session_state.gemini_api_key.strip(),
                    ):
                        temp_path = None
                        try:
                            suffix = "." + receipt.name.rsplit(".", 1)[-1].lower() if "." in receipt.name else ".png"

                            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                                tmp.write(receipt.getvalue())
                                temp_path = tmp.name

                            with st.spinner("Reading receipt and extracting grocery items..."):
                                result = extract_receipt(
                                    temp_path,
                                    gemini_api_key=st.session_state.gemini_api_key.strip(),
                                    groq_api_key=st.session_state.groq_api_key.strip() or None,
                                )

                            st.session_state.receipt_extraction_source = result.source
                            st.session_state.receipt_ocr_text = result.ocr_text

                            if result.extraction is not None:
                                st.session_state.review_items = build_receipt_review_items(result.extraction)

                                if result.source == "gemini":
                                    st.success("Receipt extracted with Gemini. Review every item before adding it to your pantry.")
                                elif result.source == "groq_fallback":
                                    st.warning("Gemini failed, so ChefNova used Groq fallback. Review the extracted items carefully.")

                                flagged = sum(
                                    1 for item in st.session_state.review_items
                                    if item.get("Needs Review")
                                )
                                if flagged:
                                    st.warning(f"{flagged} extracted item(s) need review before being added to your pantry.")
                            else:
                                st.warning("AI extraction was unavailable. Review the OCR text and enter the grocery items manually.")
                                if result.ocr_text:
                                    with st.expander("View OCR text"):
                                        st.text(result.ocr_text)

                        except Exception as exc:
                            st.error(f"Receipt extraction failed: {exc}")
                        finally:
                            if temp_path:
                                try:
                                    Path(temp_path).unlink(missing_ok=True)
                                except Exception:
                                    pass

            with type_tab:
                manual_text = st.text_area(
                    "Enter groceries naturally",
                    placeholder="e.g. eggs, milk, 2 tomatoes, one bag of spinach, 3 bananas",
                    height=110,
                )
                if st.button("Parse typed groceries", key="parse_manual", use_container_width=True):
                    parsed = parse_grocery_text(manual_text)
                    if parsed:
                        st.session_state.review_items = parsed
                        st.success(f"Parsed {len(parsed)} item(s). Review them below before adding them.")
                    else:
                        st.warning("I couldn't find grocery items in that text. Try separating items with commas.")

            with voice_tab:
                st.caption("Say something like: ‘I have rice, two cans of chickpeas, four tomatoes and a bag of spinach.’")
                inventory_audio = st.audio_input("Record grocery list", key="inventory_audio")
                if inventory_audio is not None:
                    audio_hash = hash(inventory_audio.getvalue())
                    if audio_hash != st.session_state.last_inventory_audio_hash:
                        transcript, error = speech_to_text(inventory_audio)
                        st.session_state.last_inventory_audio_hash = audio_hash
                        if error:
                            st.warning(error)
                        elif transcript:
                            st.success(f"Heard: {transcript}")
                            parsed = parse_grocery_text(transcript)
                            if parsed:
                                st.session_state.review_items = parsed
                                st.info("I converted the voice input into structured grocery items. Review them below.")

        with right:
            st.markdown('<div class="section-title">2. Review before adding</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="small-note">Nothing becomes part of your pantry until you review it and choose <b>Add reviewed items</b>.</div>',
                unsafe_allow_html=True,
            )

            review_columns = [
                "Ingredient",
                "Quantity",
                "Unit",
                "Package Size",
                "Brand",
                "Confidence",
                "Needs Review",
                "Review Reason",
            ]

            review_df = pd.DataFrame(st.session_state.review_items)
            for column in review_columns:
                if column not in review_df.columns:
                    review_df[column] = ""
            review_df = review_df[review_columns]

            edited_review_df = st.data_editor(
                review_df,
                use_container_width=True,
                num_rows="dynamic",
                hide_index=True,
                key="review_editor",
                column_config={
                    "Ingredient": st.column_config.TextColumn("Ingredient", required=True),
                    "Quantity": st.column_config.NumberColumn("Quantity", min_value=0.0, step=1.0),
                    "Unit": st.column_config.TextColumn("Unit"),
                    "Package Size": st.column_config.TextColumn("Package Size"),
                    "Brand": st.column_config.TextColumn("Brand"),
                    "Confidence": st.column_config.NumberColumn("Confidence", min_value=0.0, max_value=1.0, step=0.01, disabled=True),
                    "Needs Review": st.column_config.CheckboxColumn("Needs Review", disabled=True),
                    "Review Reason": st.column_config.TextColumn("Review Reason", disabled=True),
                },
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Add reviewed items", use_container_width=True, disabled=edited_review_df.empty):
                    reviewed = edited_review_df.fillna("").to_dict("records")
                    reviewed = [
                        {
                            "Ingredient": row.get("Ingredient", ""),
                            "Quantity": row.get("Quantity", ""),
                            "Unit": row.get("Unit", ""),
                        }
                        for row in reviewed
                        if str(row.get("Ingredient", "")).strip()
                    ]
                    merge_inventory_items(reviewed)
                    st.session_state.review_items = []
                    st.success("Reviewed items were added. Confirm the pantry after checking the final list.")
                    st.rerun()
            with c2:
                if st.button("Clear review", use_container_width=True, disabled=edited_review_df.empty):
                    st.session_state.review_items = []
                    st.rerun()

    with pantry_tab:
        st.markdown('<div class="section-title">Current pantry — source of truth</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="small-note">Edit names, quantities, or units directly. You can also add/delete rows. Saving changes marks the pantry as needing confirmation.</div>',
            unsafe_allow_html=True,
        )

        inventory_df = pd.DataFrame(st.session_state.inventory, columns=["Ingredient", "Quantity", "Unit"])
        edited_inventory_df = st.data_editor(
            inventory_df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="inventory_editor",
            column_config={
                "Ingredient": st.column_config.TextColumn("Ingredient", required=True),
                "Quantity": st.column_config.NumberColumn("Quantity", min_value=0.0, step=1.0),
                "Unit": st.column_config.TextColumn("Unit"),
            },
        )

        save_col, confirm_col = st.columns(2)
        with save_col:
            if st.button("Save pantry edits", use_container_width=True):
                cleaned = []
                for row in edited_inventory_df.fillna("").to_dict("records"):
                    if str(row.get("Ingredient", "")).strip():
                        cleaned.append(
                            {
                                "Ingredient": str(row["Ingredient"]).strip().title(),
                                "Quantity": clean_number(row.get("Quantity", 1), 1),
                                "Unit": str(row.get("Unit", "count") or "count").strip(),
                            }
                        )
                st.session_state.inventory = cleaned
                st.session_state.confirmed = False
                st.success("Pantry edits saved. Please confirm the inventory.")
                st.rerun()

        with confirm_col:
            if st.button("✓ Confirm Inventory", use_container_width=True, disabled=len(st.session_state.inventory) == 0):
                st.session_state.confirmed = True
                st.toast("Inventory confirmed. ChefNova will now use it for recipe feasibility.")
                st.rerun()

        status = "Confirmed" if st.session_state.confirmed else "Needs review"
        st.info(f"Inventory status: **{status}** · {len(st.session_state.inventory)} item(s)")


# ---------- Get Recipe ----------
def show_get_recipe():
    st.markdown('<div class="page-title">Get Recipe</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Describe the meal you want, then tell ChefNova which preferences are hard requirements and which should influence ranking.</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.confirmed:
        st.warning("Your inventory is not confirmed. Confirm it first so ChefNova can accurately label recipes as Cook now / Almost ready.")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">What would you like to cook?</div>', unsafe_allow_html=True)

    st.session_state.request = st.text_area(
        "Meal request",
        value=st.session_state.request,
        placeholder="e.g. I want a quick spicy vegetarian dinner with lots of protein...",
        height=100,
        label_visibility="collapsed",
    )

    st.markdown('<div class="section-title" style="font-size:15px;">Hard filters</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.selectbox("Diet", ["No preference", "Vegetarian", "Vegan"], key="diet_pref")
    with c2:
        st.selectbox("Maximum cooking time", ["15 min", "20 min", "30 min", "45 min", "No limit"], key="max_time_pref")
    st.text_input(
        "Avoid ingredients",
        key="avoid_pref",
        placeholder="peanuts, shellfish",
        help="Recipes that list these ingredients are dropped. This is a hard filter.",
    )

    st.markdown('<div class="section-title" style="font-size:15px;">Ranking preferences</div>', unsafe_allow_html=True)
    c3, c4, c5 = st.columns([1, 1.3, 1])
    with c3:
        st.selectbox("Cuisine", ["Any", "Indian", "Mediterranean", "Asian"], key="cuisine_pref")
    with c4:
        st.selectbox(
            "Prioritize",
            ["Best pantry match", "Fastest", "Highest protein", "Fewest missing ingredients"],
            key="priority_pref",
        )
    with c5:
        st.checkbox("Prefer high protein", key="high_protein_pref")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Rank My Recipes  →", use_container_width=True):
        if not st.session_state.confirmed:
            st.warning("Confirm your inventory first so ChefNova knows what you actually have.")
        else:
            st.session_state.temporary_exclusions = []
            st.session_state.conversation_max_time = None
            st.session_state.conversation_keywords = []
            st.session_state.messages = []
            refresh_recommendations()
            st.session_state.page = "Recommendations"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        f"Ranking asks {RECIPE_MODEL} using the Gemini key from the receipt tab, or GEMINI_API_KEY. "
        "Diet, time, and avoid are hard filters. An empty pantry or a missing key is not sent."
    )


# ---------- Recommendations ----------
def _esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def _time_label(recipe):
    minutes = recipe.get("time")
    return "time not listed" if minutes is None else f"{minutes} min"


def _protein_label(recipe):
    protein = recipe.get("protein")
    return "protein not listed" if protein is None else f"{protein}g protein"


def recipe_card(result, key):
    recipe = result["recipe"]
    if not result["missing"]:
        missing_note = "No required ingredients missing"
    else:
        missing_note = "Missing: " + ", ".join(str(item) for item in result["missing"])
    notes = " ".join(result.get("field_notes") or [])
    if notes:
        missing_note = f"{missing_note}. {notes}"
    diet = recipe.get("diet") or "diet not listed"
    tags = "".join(f'<span class="pill">{_esc(tag)}</span>' for tag in recipe.get("tags") or [])
    st.markdown(
        f"""
        <div class="recipe-card">
            <div class="recipe-image">{_esc(recipe.get('emoji') or '🍽️')}</div>
            <div class="recipe-body">
                <div class="score-badge">{result['score']}% pantry match</div><br>
                <span class="{result['status_class']}">{_esc(result['status'])}</span>
                <div class="recipe-name" style="margin-top:10px;">{_esc(recipe.get('title'))}</div>
                <div class="recipe-meta">⏱ {_esc(_time_label(recipe))} &nbsp; · &nbsp; 💪 {_esc(_protein_label(recipe))} &nbsp; · &nbsp; {_esc(diet)}</div>
                <div>{tags}</div>
                <div class="recipe-reason"><b>Why this?</b> {_esc(result['reason'])}<br>{_esc(missing_note)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("View recipe", key=key, use_container_width=True):
        st.session_state.selected_recipe = result
        st.session_state.selected_recipe_id = recipe.get("id")
        st.session_state.page = "Recipe Details"
        st.rerun()


def show_recommendations():
    st.markdown('<div class="page-title">Recommendations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Gemini proposes recipes from your confirmed pantry. Diet, time, and avoid ingredients then drop anything that breaks a hard filter. The percent on each card is pantry overlap.</div>',
        unsafe_allow_html=True,
    )

    chips = [st.session_state.diet_pref, st.session_state.max_time_pref, st.session_state.priority_pref]
    if st.session_state.cuisine_pref != "Any":
        chips.append(st.session_state.cuisine_pref)
    if st.session_state.high_protein_pref:
        chips.append("High protein preferred")
    if (st.session_state.avoid_pref or "").strip():
        chips.append("Avoid: " + st.session_state.avoid_pref.strip())
    if st.session_state.temporary_exclusions:
        chips.append("Also avoiding: " + ", ".join(st.session_state.temporary_exclusions))
    st.markdown("".join(f'<span class="pill">{_esc(chip)}</span>' for chip in chips), unsafe_allow_html=True)

    if st.session_state.recommendation_error:
        st.error(st.session_state.recommendation_error)
    elif st.session_state.recommendation_notice:
        st.info(st.session_state.recommendation_notice)

    if st.session_state.recommendation_candidates is None and not st.session_state.recommendation_error:
        st.info("Rank recipes from Get Recipe. Nothing is invented before Gemini answers.")
        recipes = []
    else:
        recipes = visible_recommendations()
        if st.session_state.recommendation_error:
            pass
        elif not st.session_state.recommendation_candidates:
            st.warning("Gemini returned no recipes. No meals were invented to fill the gap.")
        elif not recipes:
            st.warning("No returned recipes satisfy the current hard filters. Try a longer time, a different diet, or a shorter avoid list.")

    if recipes:
        st.markdown('<div class="section-title">ChefNova recommends</div>', unsafe_allow_html=True)
        top_results = recipes[:3]
        cols = st.columns(len(top_results), gap="medium")
        for i, (col, result) in enumerate(zip(cols, top_results)):
            with col:
                recipe_card(result, key=f"view_{result['recipe']['id']}_{i}")

        with st.expander("How is the match calculated?"):
            st.markdown(
                f"""
                Gemini `{RECIPE_MODEL}` proposes up to four recipes from the confirmed pantry.
                The app then checks that JSON locally.

                - **Cook now** means every listed ingredient is already in the pantry.
                - **Almost ready** means one or two ingredients are missing.
                - **Needs shopping** means three or more ingredients are missing, or the ingredient list was blank.
                - The percent is that pantry overlap. Diet, maximum time, and avoid ingredients are hard filters.
                - A missing time or protein stays visible and is marked. It is not filled in.
                - Chat refinements reorder or hide this list. Ask Gemini again when you want a new set.
                """
            )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div style="font-size:19px;font-weight:650;margin-bottom:5px;">Ask ChefNova</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="small-note" style="margin-bottom:9px;">Refine the current results without restarting. Temporary statements do not silently change your confirmed pantry.</div>',
        unsafe_allow_html=True,
    )

    refine_text = st.chat_input("e.g. I don't have spinach · make it under 15 minutes · something spicy")
    if refine_text:
        process_refinement(refine_text)
        st.rerun()

    audio = st.audio_input("Or refine by voice", key="recommendation_audio")
    if audio is not None:
        audio_hash = hash(audio.getvalue())
        if audio_hash != st.session_state.last_refine_audio_hash:
            transcript, error = speech_to_text(audio)
            st.session_state.last_refine_audio_hash = audio_hash
            if error:
                st.warning(error)
            elif transcript:
                process_refinement(transcript)
                st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])

    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("Ask Gemini again", use_container_width=True):
            if not st.session_state.confirmed:
                st.warning("Confirm your inventory before asking again.")
            else:
                refresh_recommendations()
                st.rerun()
    with action_right:
        if st.session_state.temporary_exclusions or st.session_state.conversation_max_time or st.session_state.conversation_keywords:
            if st.button("Reset conversational refinements", use_container_width=True):
                st.session_state.temporary_exclusions = []
                st.session_state.conversation_max_time = None
                st.session_state.conversation_keywords = []
                st.session_state.messages = []
                st.rerun()


# ---------- Recipe details ----------
def show_recipe_details():
    selected = st.session_state.selected_recipe
    if not selected or not selected.get("recipe"):
        st.warning("Choose a recipe from Recommendations first.")
        if st.button("← Back to recommendations"):
            st.session_state.page = "Recommendations"
            st.rerun()
        return

    recipe = selected["recipe"]
    checked = rank_recipes([recipe], current_constraints(), st.session_state.inventory)
    result = checked[0] if checked else None
    available = inventory_names(include_temporary_exclusions=True)
    ingredients = recipe.get("ingredients") or []
    missing = [item for item in ingredients if normalize_name(item) not in available]
    present = [item for item in ingredients if normalize_name(item) in available]
    diet = recipe.get("diet") or "diet not listed"
    field_notes = selected.get("field_notes") or []

    st.markdown(f'<div class="page-title">{_esc(recipe.get("title"))}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-subtitle">{_esc(_time_label(recipe))} · {_esc(_protein_label(recipe))} · {_esc(diet)} · Source: {_esc(recipe.get("source"))}</div>',
        unsafe_allow_html=True,
    )
    if field_notes:
        st.warning(" ".join(field_notes))

    left, right = st.columns([1.55, 1], gap="large")
    with left:
        st.markdown(
            f'<div class="card"><div style="font-size:54px;text-align:center;padding:18px;">{_esc(recipe.get("emoji") or "🍽️")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-title">Ingredients</div>', unsafe_allow_html=True)
        if not ingredients:
            st.markdown("- Ingredients were not returned.")
        for ingredient in ingredients:
            symbol = "✓" if normalize_name(ingredient) in available else "!"
            st.markdown(f"- {symbol} {_esc(ingredient)}")

        st.markdown('<div class="section-title">Steps</div>', unsafe_allow_html=True)
        steps = recipe.get("instructions") or []
        if not steps:
            st.markdown("Steps were not returned.")
        for i, step in enumerate(steps, start=1):
            st.markdown(f"**{i}.** {_esc(step)}")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        if result:
            score_text = f"{result['score']}% pantry match"
            reason = result["reason"]
        else:
            score_text = "Filtered by current constraints"
            reason = "This recipe no longer matches the current hard filters."
        st.markdown(
            f"""
            <div class="card">
                <div class="small-note">WHY CHEFNOVA RECOMMENDED THIS</div>
                <div style="font-size:23px;font-weight:700;margin-top:8px;">{_esc(score_text)}</div>
                <div class="small-note" style="margin-top:10px;">
                    {_esc(reason)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="small-note">INVENTORY CHECK</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="available">✓ Available: {_esc(", ".join(present) if present else "None of the required ingredients")}</div>',
            unsafe_allow_html=True,
        )
        if missing:
            st.markdown(
                f'<div class="missing">! Missing: {_esc(", ".join(missing))}</div>',
                unsafe_allow_html=True,
            )
            substitutions = recipe.get("substitutions") or {}
            substitution_lines = []
            for item in missing:
                if item in substitutions:
                    substitution_lines.append(f"**{_esc(item)}:** try {_esc(substitutions[item])}")
            if substitution_lines:
                st.markdown("**Possible substitutions**")
                for line in substitution_lines:
                    st.markdown(f"- {line}")
        elif ingredients:
            st.success("Cook now: every required ingredient is available in your confirmed pantry.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="small-note">AFTER COOKING</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:18px;font-weight:650;margin-top:8px;">How was this recipe?</div>', unsafe_allow_html=True)
        recipe_id = recipe.get("id") or "recipe"
        f1, f2, f3 = st.columns(3)
        if f1.button("👍 Loved", key=f"love_{recipe_id}", use_container_width=True):
            st.session_state.feedback[recipe_id] = "Loved"
        if f2.button("😐 Okay", key=f"okay_{recipe_id}", use_container_width=True):
            st.session_state.feedback[recipe_id] = "Okay"
        if f3.button("👎 No", key=f"no_{recipe_id}", use_container_width=True):
            st.session_state.feedback[recipe_id] = "Disliked"
        if recipe_id in st.session_state.feedback:
            st.caption(f"Saved feedback: {st.session_state.feedback[recipe_id]}. This can be used for future personalization.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to recommendations", use_container_width=True):
            st.session_state.page = "Recommendations"
            st.rerun()


# ---------- Evaluation plan ----------
def show_evaluation_plan():
    st.markdown('<div class="page-title">Evaluation Plan</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">A concrete testing plan addresses the feedback asking us to define receipt sources, recipe sources, and measurable accuracy targets.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Receipt test set</div>', unsafe_allow_html=True)
        st.markdown(
            """
            **Suggested sources**
            - Walmart
            - Target
            - Costco
            - Aldi
            - Instacart / grocery-order screenshots

            **Suggested conditions**
            - clear digital receipt
            - clear phone photo
            - slightly blurry / folded receipt
            - long receipt
            - mixed grocery + non-food receipt

            Start with **20–30 receipts** so the team can manually create ground-truth labels and calculate precision/recall.
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Recipe source</div>', unsafe_allow_html=True)
        st.markdown(
            """
            **Current ranking:** Gemini proposes recipes from the confirmed pantry. The app then applies diet, time, and avoid filters and labels Cook now, Almost ready, and Needs shopping from ingredient overlap. Invalid model output shows an error and no recipes.

            A licensed recipe catalog, such as Spoonacular or TheMealDB, can still replace free generation later. Until then, every shown recipe comes from a Gemini response that passed the JSON checks.
            """
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Target metrics</div>', unsafe_allow_html=True)
    metric_df = pd.DataFrame(
        [
            ["Grocery item precision", "≥ 90%", "Of extracted grocery items, how many are truly groceries?"],
            ["Grocery item recall", "≥ 85%", "Of true grocery items, how many were extracted?"],
            ["Quantity extraction accuracy", "≥ 80%", "Was the quantity parsed correctly?"],
            ["Manual / voice parsing accuracy", "≥ 90%", "Did natural language become the correct structured items?"],
            ["Dietary compliance", "100% target", "Hard dietary filters should never be violated."],
            ["Cook-now feasibility", "≥ 95%", "Recipes labeled Cook now should truly require no missing core ingredients."],
            ["Top-3 recommendation relevance", "≥ 80% positive", "Users find at least one top recommendation acceptable."],
        ],
        columns=["Metric", "Target", "Meaning"],
    )
    st.dataframe(metric_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------- Router ----------
if st.session_state.page == "Home":
    show_home()
elif st.session_state.page == "My Inventory":
    show_inventory()
elif st.session_state.page == "Get Recipe":
    show_get_recipe()
elif st.session_state.page == "Recommendations":
    show_recommendations()
elif st.session_state.page == "Recipe Details":
    show_recipe_details()
elif st.session_state.page == "Evaluation Plan":
    show_evaluation_plan()
else:
    st.session_state.page = "Home"
    st.rerun()
