import html
import io
import re
from copy import deepcopy

import pandas as pd
import streamlit as st

try:
    import speech_recognition as sr
except ImportError:
    sr = None

from pantry_extraction import (
    confirm_review_into_inventory,
    extract_receipt,
    issue_text,
    validate_row,
)
from pantry_extraction.gemini import GeminiReceiptModel
from pantry_extraction.key_store import prefill_api_key, save_api_key
from recipe_recommendation import Constraints, rank_recipes, recommend_recipes
from recipe_recommendation.gemini import GeminiRecipeModel


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
        "extraction_error": None,
        "extraction_notice": None,
        "avoid_pref": "",
        "recommendation_candidates": None,
        "recommendation_error": None,
        "recommendation_notice": None,
        "recommendation_model": None,
        "selected_recipe": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# ---------- Helpers ----------
def normalize_name(name):
    return re.sub(r"\s+", " ", str(name).strip()).lower()


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


def _mime_type(upload) -> str:
    media_type = getattr(upload, "type", None) or ""
    if media_type in {"image/png", "image/jpeg", "image/jpg", "application/pdf"}:
        return "image/jpeg" if media_type == "image/jpg" else media_type
    name = (getattr(upload, "name", "") or "").lower()
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith(".jpg") or name.endswith(".jpeg"):
        return "image/jpeg"
    return media_type or "application/octet-stream"


def _rows_from_extraction(result):
    rows = []
    for item in result.items:
        row = item.as_review_dict()
        row["missing_fields"] = list(item.missing_fields)
        rows.append(row)
    return rows


def run_receipt_extraction(upload, api_key):
    """Extract into review rows using the key from the scan prompt. Inventory is unchanged."""
    key = str(api_key or "").strip()
    if not key:
        return [], "Enter a Gemini API key to read this receipt. No items were added.", None
    model = GeminiReceiptModel(api_key=key)
    result = extract_receipt(upload.getvalue(), _mime_type(upload), model)
    if not result.ok:
        return [], result.failure_reason, None
    notice = result.notice
    if model.model_used and model.model_used != model._model:
        fallback = f"Gemini used {model.model_used} because {model._model} was busy."
        notice = f"{notice} {fallback}" if notice else fallback
    return _rows_from_extraction(result), None, notice


def effective_max_time():
    if st.session_state.conversation_max_time:
        return st.session_state.conversation_max_time
    value = st.session_state.max_time_pref
    if value == "No limit":
        return None
    return int(value.split()[0])


def constraints_from_session():
    avoid = [part.strip() for part in str(st.session_state.avoid_pref).split(",") if part.strip()]
    avoid.extend(st.session_state.temporary_exclusions)
    request = st.session_state.request.strip()
    if st.session_state.conversation_keywords:
        extra = ", ".join(st.session_state.conversation_keywords)
        request = f"{request}\nAlso prefer: {extra}".strip()
    return Constraints(
        diet=st.session_state.diet_pref,
        max_minutes=effective_max_time(),
        avoid=avoid,
        cuisine=st.session_state.cuisine_pref,
        priority=st.session_state.priority_pref,
        high_protein=bool(st.session_state.high_protein_pref),
        request=request,
    )


def current_recommendation_cards():
    candidates = st.session_state.recommendation_candidates or []
    return rank_recipes(candidates, constraints_from_session(), st.session_state.inventory)


def run_recipe_ranking(api_key):
    """One Gemini call. Later filters reuse the stored recipes."""
    model = GeminiRecipeModel(api_key=api_key)
    result = recommend_recipes(st.session_state.inventory, constraints_from_session(), model)
    st.session_state.recommendation_candidates = result.candidates
    st.session_state.recommendation_error = result.error
    st.session_state.recommendation_notice = result.notice
    st.session_state.recommendation_model = model.model_used
    return result.ok


def extract_known_ingredient_from_message(text):
    names = {normalize_name(item["Ingredient"]) for item in st.session_state.inventory}
    for recipe in st.session_state.recommendation_candidates or []:
        for ingredient in recipe.get("ingredients") or []:
            names.add(normalize_name(ingredient))
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
    reply = "I applied that to the recipes Gemini already returned. Rank again if you want a new set."

    ingredient = extract_known_ingredient_from_message(text)
    negative_patterns = ["don't have", "do not have", "no ", "without ", "don't want", "do not want"]
    if ingredient and any(pattern in lower for pattern in negative_patterns):
        if ingredient not in st.session_state.temporary_exclusions:
            st.session_state.temporary_exclusions.append(ingredient)
        reply = (
            f"I removed recipes that use {ingredient}. "
            "The confirmed pantry was not changed."
        )
    else:
        minute_match = re.search(r"(\d{1,2})\s*(?:min|minute)", lower)
        if minute_match:
            st.session_state.conversation_max_time = int(minute_match.group(1))
            reply = f"I kept only Gemini recipes that take {minute_match.group(1)} minutes or less."
        elif "spicy" in lower:
            if "spicy" not in st.session_state.conversation_keywords:
                st.session_state.conversation_keywords.append("spicy")
            reply = "I noted spicy for the next ranking. Choose Ask Gemini again to generate a new set."
        elif "quick" in lower or "faster" in lower:
            st.session_state.priority_pref = "Fastest"
            reply = "I reordered these Gemini recipes toward the fastest ones."
        elif "protein" in lower:
            st.session_state.high_protein_pref = True
            st.session_state.priority_pref = "Highest protein"
            reply = "I reordered these Gemini recipes toward higher protein."

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
                    <div style="font-size:25px;">💬</div>
                    <div style="font-size:18px;font-weight:650;margin-top:7px;">Cook your way</div>
                    <div class="small-note" style="margin-top:6px;">Tell ChefNova what you want, refine the recommendations, and choose the recipe that works for you.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Get a Recipe", key="home_preferences", use_container_width=True):
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
                receipt = st.file_uploader(
                    "Upload a receipt or grocery-order screenshot",
                    type=["png", "jpg", "jpeg", "pdf"],
                    help="Each scan asks for a Gemini API key before extraction. Items stay in this review table until you confirm them.",
                )
                if receipt is not None:
                    st.success(f"Receipt ready: {receipt.name}")
                    receipt_id = f"{receipt.name}:{getattr(receipt, 'size', 0)}"
                    key_widget = f"gemini_key_{receipt_id}"
                    save_widget = f"gemini_save_{receipt_id}"
                    if key_widget not in st.session_state:
                        prefilled, source = prefill_api_key()
                        st.session_state[key_widget] = prefilled
                        st.session_state[f"gemini_source_{receipt_id}"] = source
                    source = st.session_state.get(f"gemini_source_{receipt_id}", "none")
                    if source == "saved":
                        st.caption("A key saved on this computer is filled in. Reuse it, edit it, or replace it. Nothing is sent until you extract.")
                    elif source == "env":
                        st.caption("Filled in from GEMINI_API_KEY. Save it below if this computer should remember it. Nothing is sent until you extract.")
                    else:
                        st.caption("Enter a Gemini API key for this scan. Nothing is sent until you extract.")
                    st.text_input(
                        "Gemini API key",
                        type="password",
                        key=key_widget,
                        autocomplete="off",
                    )
                    st.checkbox("Save this key on this computer for later scans", key=save_widget)
                    if st.button("Extract grocery items", key="extract_receipt", use_container_width=True):
                        typed_key = st.session_state.get(key_widget, "")
                        if st.session_state.get(save_widget) and str(typed_key).strip():
                            save_api_key(typed_key)
                        rows, error, notice = run_receipt_extraction(receipt, typed_key)
                        st.session_state.review_items = rows
                        st.session_state.extraction_error = error
                        st.session_state.extraction_notice = notice
                        st.rerun()

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
                        st.session_state.extraction_error = None
                        st.session_state.extraction_notice = "Review the typed items below. They are not in the pantry until you confirm them."
                        st.success(f"Parsed {len(parsed)} item(s). Review them below before confirming.")
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
                                st.session_state.extraction_error = None
                                st.session_state.extraction_notice = "Review the voice items below. They are not in the pantry until you confirm them."
                                st.info("I converted the voice input into structured grocery items. Review them below.")

        with right:
            st.markdown('<div class="section-title">2. Review before adding</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="small-note">Nothing becomes part of your pantry until every row has a valid name, quantity, and unit and you choose <b>Confirm reviewed items</b>.</div>',
                unsafe_allow_html=True,
            )
            if st.session_state.extraction_error:
                st.error(st.session_state.extraction_error)
            elif st.session_state.extraction_notice:
                st.info(st.session_state.extraction_notice)

            review_df = pd.DataFrame(st.session_state.review_items, columns=["Ingredient", "Quantity", "Unit"])
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
                },
            )

            pending = edited_review_df.fillna("").to_dict("records")
            for row in pending:
                item = validate_row(row)
                if not item.ok:
                    label = item.name or "This row"
                    st.warning(f"{label}: {issue_text(item)}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Confirm reviewed items", use_container_width=True, disabled=edited_review_df.empty):
                    outcome = confirm_review_into_inventory(st.session_state.inventory, pending)
                    if not outcome.accepted:
                        st.error(outcome.message)
                    else:
                        st.session_state.inventory = outcome.inventory
                        st.session_state.confirmed = False
                        st.session_state.review_items = []
                        st.session_state.extraction_error = None
                        st.session_state.extraction_notice = None
                        st.success(outcome.message)
                        st.rerun()
            with c2:
                if st.button("Clear review", use_container_width=True, disabled=edited_review_df.empty):
                    st.session_state.review_items = []
                    st.session_state.extraction_error = None
                    st.session_state.extraction_notice = None
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
        "Avoid",
        key="avoid_pref",
        placeholder="peanuts, shellfish",
        help="Allergies and other ingredients. A recipe that includes one is removed.",
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

    saved_key, key_source = prefill_api_key()
    if not saved_key:
        st.caption("Recipe ranking needs a Gemini key. Save it here and receipt scans can reuse it. Nothing is sent until you rank.")
        st.text_input("Gemini API key", type="password", key="recipe_gemini_key", autocomplete="off")
        st.checkbox("Save this key on this computer for later", key="recipe_gemini_save")
    elif key_source == "saved":
        st.caption("Recipe ranking uses the Gemini key already saved on this computer. Nothing is sent until you rank.")
    else:
        st.caption("Recipe ranking uses GEMINI_API_KEY. Nothing is sent until you rank.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Rank My Recipes  →", use_container_width=True):
        if not st.session_state.confirmed:
            st.warning("Confirm your inventory first so ChefNova knows what you actually have.")
        elif not any(str(item.get("Ingredient", "")).strip() for item in st.session_state.inventory):
            st.warning("Add at least one pantry item before ranking. No recipes were invented.")
        else:
            api_key = saved_key or str(st.session_state.get("recipe_gemini_key", "")).strip()
            if not api_key:
                st.error("Add a Gemini API key to rank recipes. Nothing was sent.")
            else:
                if not saved_key and st.session_state.get("recipe_gemini_save") and api_key:
                    save_api_key(api_key)
                st.session_state.temporary_exclusions = []
                st.session_state.conversation_max_time = None
                st.session_state.conversation_keywords = []
                st.session_state.messages = []
                run_recipe_ranking(api_key)
                st.session_state.page = "Recommendations"
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        "Hard filters remove incompatible recipes. Ranking preferences change the order of the remaining recipes instead of silently violating your constraints."
    )


# ---------- Recommendations ----------
def _recipe_meta(recipe):
    if recipe.get("time") is None:
        time_bit = "time not listed"
    else:
        time_bit = f"{recipe['time']} min"
    if recipe.get("protein") is None:
        protein_bit = "protein not listed"
    else:
        protein_bit = f"{recipe['protein']}g protein"
    diet_bit = recipe.get("diet") or "diet not listed"
    return time_bit, protein_bit, diet_bit


def recipe_card(result, key):
    recipe = result["recipe"]
    time_bit, protein_bit, diet_bit = _recipe_meta(recipe)
    missing_note = "No required ingredients missing" if not result["missing"] else "Missing: " + ", ".join(result["missing"])
    field_notes = "".join(f"<br>{html.escape(note)}" for note in result.get("field_notes") or [])
    tags = "".join(f'<span class="pill">{html.escape(str(tag))}</span>' for tag in recipe.get("tags") or [])
    st.markdown(
        f"""
        <div class="recipe-card">
            <div class="recipe-image">{html.escape(recipe.get('emoji') or '🍽️')}</div>
            <div class="recipe-body">
                <span class="{result['status_class']}">{html.escape(result['status'])}</span>
                <div class="recipe-name" style="margin-top:10px;">{html.escape(recipe['title'])}</div>
                <div class="recipe-meta">⏱ {html.escape(time_bit)} &nbsp; · &nbsp; 💪 {html.escape(protein_bit)} &nbsp; · &nbsp; {html.escape(diet_bit)}</div>
                <div>{tags}</div>
                <div class="recipe-reason"><b>Why this?</b> {html.escape(result['reason'])}<br>{html.escape(missing_note)}{field_notes}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("View recipe", key=key, use_container_width=True):
        st.session_state.selected_recipe_id = recipe["id"]
        st.session_state.selected_recipe = result
        st.session_state.page = "Recipe Details"
        st.rerun()


def show_recommendations():
    st.markdown('<div class="page-title">Recommendations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">ChefNova uses your confirmed pantry and meal preferences to find recipes that fit what you can realistically cook.</div>',
        unsafe_allow_html=True,
    )

    chips = [st.session_state.diet_pref, st.session_state.max_time_pref, st.session_state.priority_pref]
    if st.session_state.cuisine_pref != "Any":
        chips.append(st.session_state.cuisine_pref)
    if st.session_state.high_protein_pref:
        chips.append("High protein preferred")
    if str(st.session_state.avoid_pref).strip():
        chips.append("Avoid: " + st.session_state.avoid_pref.strip())
    if st.session_state.temporary_exclusions:
        chips.append("Avoiding: " + ", ".join(st.session_state.temporary_exclusions))
    st.markdown("".join(f'<span class="pill">{html.escape(str(chip))}</span>' for chip in chips), unsafe_allow_html=True)
    if st.session_state.recommendation_model:
        st.caption(
            f"Last ranking model: {st.session_state.recommendation_model}. "
            "Pantry match, diet, time, and avoid are checked again on this page."
        )

    if st.session_state.recommendation_error:
        st.error(st.session_state.recommendation_error)
    elif st.session_state.recommendation_candidates is None:
        st.info("Rank My Recipes to ask Gemini. Nothing is sent until you do.")
    else:
        recipes = current_recommendation_cards()
        if not recipes:
            st.warning(
                st.session_state.recommendation_notice
                or "No recipes satisfy all current hard filters. Try increasing the time limit or changing the diet or avoid list."
            )
        else:
            st.markdown('<div class="section-title">ChefNova recommends</div>', unsafe_allow_html=True)
            top_results = recipes[:3]
            cols = st.columns(len(top_results), gap="medium")
            for i, (col, result) in enumerate(zip(cols, top_results)):
                with col:
                    recipe_card(result, key=f"view_{result['recipe']['id']}_{i}")

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

    again, reset = st.columns(2)
    if again.button("Ask Gemini again", use_container_width=True):
        key, _source = prefill_api_key()
        if not key:
            key = str(st.session_state.get("recipe_gemini_key", "")).strip()
        if not key:
            st.error("Add a Gemini API key on Get Recipe. Nothing was sent.")
        elif not st.session_state.confirmed:
            st.warning("Confirm your inventory first.")
        else:
            run_recipe_ranking(key)
            st.rerun()
    if reset.button("Reset conversational refinements", use_container_width=True):
        st.session_state.temporary_exclusions = []
        st.session_state.conversation_max_time = None
        st.session_state.conversation_keywords = []
        st.session_state.messages = []
        st.rerun()


# ---------- Recipe details ----------
def show_recipe_details():
    result = st.session_state.selected_recipe
    if not result:
        st.warning("Choose a recipe from Recommendations first.")
        if st.button("← Back to recommendations"):
            st.session_state.page = "Recommendations"
            st.rerun()
        return

    recipe = result["recipe"]
    missing = list(result.get("missing") or [])
    present = [item for item in recipe.get("ingredients") or [] if item not in missing]
    time_bit, protein_bit, diet_bit = _recipe_meta(recipe)

    st.markdown(f'<div class="page-title">{html.escape(recipe["title"])}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="page-subtitle">{html.escape(time_bit)} · {html.escape(protein_bit)} · {html.escape(diet_bit)} · Source: {html.escape(recipe.get("source") or "Gemini")}</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.55, 1], gap="large")
    with left:
        st.markdown(
            f'<div class="card"><div style="font-size:54px;text-align:center;padding:18px;">{html.escape(recipe.get("emoji") or "🍽️")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-title">Ingredients</div>', unsafe_allow_html=True)
        if not recipe.get("ingredients"):
            st.markdown("- Ingredients were not returned.")
        for ingredient in recipe.get("ingredients") or []:
            symbol = "✓" if ingredient in present else "!"
            st.markdown(f"- {symbol} {html.escape(ingredient)}")

        st.markdown('<div class="section-title">Steps</div>', unsafe_allow_html=True)
        if not recipe.get("instructions"):
            st.markdown("Steps were not returned.")
        for i, step in enumerate(recipe.get("instructions") or [], start=1):
            st.markdown(f"**{i}.** {html.escape(step)}")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        notes = " ".join(result.get("field_notes") or [])
        why = result["reason"] + (f" {notes}" if notes else "")
        st.markdown(
            f"""
            <div class="card">
                <div class="small-note">WHY CHEFNOVA RECOMMENDED THIS</div>
                <div style="font-size:23px;font-weight:700;margin-top:8px;">ChefNova recommendation</div>
                <div class="small-note" style="margin-top:10px;">
                    {html.escape(why)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="small-note">INVENTORY CHECK</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="available">✓ Available: {html.escape(", ".join(present) if present else "None of the required ingredients")}</div>',
            unsafe_allow_html=True,
        )
        if missing:
            st.markdown(
                f'<div class="missing">! Missing: {html.escape(", ".join(missing))}</div>',
                unsafe_allow_html=True,
            )
            substitution_lines = []
            for item in missing:
                if item in recipe.get("substitutions", {}):
                    substitution_lines.append(
                        f"**{html.escape(item)}:** try {html.escape(recipe['substitutions'][item])}"
                    )
            if substitution_lines:
                st.markdown("**Possible substitutions**")
                for line in substitution_lines:
                    st.markdown(f"- {line}")
        else:
            st.success("Cook now: every required ingredient is available in your confirmed pantry.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="small-note">AFTER COOKING</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:18px;font-weight:650;margin-top:8px;">How was this recipe?</div>', unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)
        if f1.button("👍 Loved", key=f"love_{recipe['id']}", use_container_width=True):
            st.session_state.feedback[recipe["id"]] = "Loved"
        if f2.button("😐 Okay", key=f"okay_{recipe['id']}", use_container_width=True):
            st.session_state.feedback[recipe["id"]] = "Okay"
        if f3.button("👎 No", key=f"no_{recipe['id']}", use_container_width=True):
            st.session_state.feedback[recipe["id"]] = "Disliked"
        if recipe["id"] in st.session_state.feedback:
            st.caption(f"Saved feedback: {st.session_state.feedback[recipe['id']]}. This can be used for future personalization.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to recommendations", use_container_width=True):
            st.session_state.page = "Recommendations"
            st.rerun()


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
else:
    st.session_state.page = "Home"
    st.rerun()
