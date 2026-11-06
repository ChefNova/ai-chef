"""The Streamlit app against a real database, using Streamlit's own test runner.

Each AppTest here is a separate browser session. Reading a value back from a new
AppTest is what "persists across sessions" means for a user. No test calls a model.

AppTest cannot type into st.data_editor, so edits to the pantry table are simulated
by replacing what the editor returns. Everything after that point is the real save path.
"""

from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from app.api import app as api_app
from app.storage import PantryStore
from app.storage_models import PantryItemCreate, PreferencesUpdate

APP_FILE = str(Path(__file__).resolve().parent.parent / "ChefNova_app_UI.py")
STARTER_NAMES = {"Rice", "Chickpeas", "Spinach", "Tomatoes", "Greek Yogurt", "Garlic"}
SESSION_ONLY_KEY = "AIzaSECRET-session-only-key"


@pytest.fixture(autouse=True)
def no_ambient_keys(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


def new_session(profile=None):
    session = AppTest.from_file(APP_FILE, default_timeout=30)
    if profile:
        session.query_params["profile"] = profile
    session.run()
    assert not session.exception, session.exception
    return session


def click(session, label):
    matches = [button for button in session.button if label in button.label]
    assert matches, f"No button {label!r} in {[button.label for button in session.button]}"
    matches[0].click().run()
    assert not session.exception, session.exception


def open_get_recipe(session):
    click(session, "Get Recipe")


def pantry_names(session):
    return {row["Ingredient"] for row in session.session_state["inventory"]}


def save_edited_pantry(monkeypatch, change):
    """Click Save pantry edits while the table returns what a user would have typed into it."""
    real_editor = st.data_editor

    def fake_editor(data, *args, key=None, **kwargs):
        result = real_editor(data, *args, key=key, **kwargs)
        return change(result) if key == "inventory_editor" else result

    # A context, not monkeypatch.undo(), which would also undo the temporary database path.
    with monkeypatch.context() as patch:
        patch.setattr(st, "data_editor", fake_editor)
        session = new_session()
        click(session, "My Inventory")
        click(session, "Save pantry edits")
    return session


# ---------- First visit ----------
def test_first_visit_shows_the_documented_starter_state():
    session = new_session()
    assert pantry_names(session) == STARTER_NAMES
    assert session.session_state["confirmed"] is False
    assert session.session_state["diet_pref"] == "Vegetarian"
    assert session.session_state["max_time_pref"] == "20 min"
    assert session.session_state["cuisine_pref"] == "Any"
    assert session.session_state["priority_pref"] == "Best pantry match"
    assert session.session_state["high_protein_pref"] is True
    assert session.session_state["avoid_pref"] == ""


def test_whole_quantities_are_shown_without_a_decimal():
    quantities = {row["Ingredient"]: row["Quantity"] for row in new_session().session_state["inventory"]}
    assert quantities["Rice"] == 2
    assert isinstance(quantities["Rice"], int)


def test_every_page_renders_with_saved_data():
    session = new_session()
    for label in ("My Inventory", "Get Recipe", "Evaluation Plan", "Home"):
        click(session, label)


# ---------- Pantry persistence ----------
def test_reviewed_items_are_there_in_the_next_session():
    session = new_session()
    session.session_state["review_items"] = [{"Ingredient": "lentils", "Quantity": 3, "Unit": "cups"}]
    click(session, "My Inventory")
    click(session, "Add reviewed items")

    assert "Lentils" in pantry_names(session)
    assert session.session_state["review_items"] == []
    assert "Lentils" in pantry_names(new_session())


def test_adding_to_a_saved_item_adds_the_quantities():
    session = new_session()
    session.session_state["review_items"] = [{"Ingredient": "rice", "Quantity": 1, "Unit": "CUPS"}]
    click(session, "My Inventory")
    click(session, "Add reviewed items")
    rice = [row for row in new_session().session_state["inventory"] if row["Ingredient"] == "Rice"]
    assert rice == [{"Ingredient": "Rice", "Quantity": 3, "Unit": "cups"}]


def test_pantry_table_edits_are_there_in_the_next_session(monkeypatch):
    def change(table):
        table = table[table["Ingredient"] != "Garlic"].copy()
        table.loc[table["Ingredient"] == "Rice", "Quantity"] = 5
        extra = pd.DataFrame([{"Ingredient": "tofu", "Quantity": 1, "Unit": "block"}])
        return pd.concat([table, extra], ignore_index=True)

    save_edited_pantry(monkeypatch, change)

    saved = {row["Ingredient"]: row["Quantity"] for row in new_session().session_state["inventory"]}
    assert "Garlic" not in saved
    assert saved["Rice"] == 5
    assert saved["Tofu"] == 1


def test_emptied_pantry_stays_empty_and_is_not_seeded_again(monkeypatch):
    save_edited_pantry(monkeypatch, lambda table: table.iloc[0:0])

    returning = new_session()
    assert returning.session_state["inventory"] == []
    click(returning, "My Inventory")
    confirm = [button for button in returning.button if "Confirm Inventory" in button.label][0]
    assert confirm.disabled


def test_invalid_row_shows_an_error_and_saves_nothing():
    session = new_session()
    session.session_state["review_items"] = [
        {"Ingredient": "Good", "Quantity": 1, "Unit": "cup"},
        {"Ingredient": "x" * 200, "Quantity": 1, "Unit": "cup"},
    ]
    click(session, "My Inventory")
    click(session, "Add reviewed items")

    assert any("Nothing was saved" in error.value for error in session.error)
    assert len(session.session_state["review_items"]) == 2
    assert "Good" not in pantry_names(new_session())


def test_clear_pantry_persists_and_only_clears_current_profile():
    session = new_session()
    other = PantryStore()
    other.ensure_user("other", seed_items=[PantryItemCreate(name="Tofu", quantity=1, unit="block")])
    click(session, "My Inventory")
    click(session, "Confirm Inventory")
    session.session_state["recommendation_candidates"] = [{"title": "Old recipe"}]
    session.session_state["selected_recipe"] = {"title": "Old recipe"}
    session.session_state["selected_recipe_id"] = "old-recipe"
    click(session, "Clear pantry")

    assert session.session_state["inventory"] == []
    assert session.session_state["confirmed"] is False
    assert session.session_state["recommendation_candidates"] is None
    assert session.session_state["selected_recipe"] is None
    assert session.session_state["selected_recipe_id"] is None
    assert session.session_state["diet_pref"] == "Vegetarian"
    assert next(button for button in session.button if button.label == "Clear pantry").disabled
    assert new_session().session_state["inventory"] == []
    assert pantry_names(new_session(profile="other")) == {"Tofu"}


# ---------- Confirmation ----------
def test_confirmation_does_not_carry_over_to_a_new_session():
    """A saved pantry records what was there last time. Each visit must confirm it again."""
    session = new_session()
    click(session, "My Inventory")
    click(session, "Confirm Inventory")
    assert session.session_state["confirmed"] is True
    assert new_session().session_state["confirmed"] is False


def test_confirmation_lasts_within_a_session_while_the_pantry_is_unchanged():
    session = new_session()
    click(session, "My Inventory")
    click(session, "Confirm Inventory")
    click(session, "Home")
    click(session, "Get Recipe")
    assert session.session_state["confirmed"] is True


def test_saving_edits_clears_the_confirmation():
    session = new_session()
    click(session, "My Inventory")
    click(session, "Confirm Inventory")
    click(session, "Save pantry edits")
    assert session.session_state["confirmed"] is False


def test_change_from_another_tab_clears_the_confirmation_and_shows_up():
    session = new_session()
    click(session, "My Inventory")
    click(session, "Confirm Inventory")

    PantryStore().add_item("default", PantryItemCreate(name="Tofu", quantity=1, unit="block"))
    click(session, "Home")

    assert "Tofu" in pantry_names(session)
    assert session.session_state["confirmed"] is False


def test_ranking_without_a_new_confirmation_stays_on_get_recipe():
    new_session()
    returning = new_session()
    open_get_recipe(returning)
    click(returning, "Rank My Recipes")
    assert returning.session_state["page"] == "Get Recipe"
    assert any("Confirm your inventory first" in warning.value for warning in returning.warning)


# ---------- Preference persistence ----------
def test_preferences_are_there_in_the_next_session():
    session = new_session()
    open_get_recipe(session)
    session.selectbox(key="diet_pref").set_value("Vegan").run()
    session.selectbox(key="max_time_pref").set_value("No limit").run()
    session.selectbox(key="cuisine_pref").set_value("Indian").run()
    session.selectbox(key="priority_pref").set_value("Fastest").run()
    session.checkbox(key="high_protein_pref").set_value(False).run()
    session.text_input(key="avoid_pref").set_value("peanuts; shellfish").run()
    assert not session.exception

    returning = new_session()
    open_get_recipe(returning)
    assert returning.selectbox(key="diet_pref").value == "Vegan"
    assert returning.selectbox(key="max_time_pref").value == "No limit"
    assert returning.selectbox(key="cuisine_pref").value == "Indian"
    assert returning.selectbox(key="priority_pref").value == "Fastest"
    assert returning.checkbox(key="high_protein_pref").value is False
    assert returning.text_input(key="avoid_pref").value == "peanuts, shellfish"


def test_clearing_the_avoid_list_is_saved():
    PantryStore().ensure_user("default")
    PantryStore().update_preferences("default", PreferencesUpdate(dietary_restrictions=["peanuts"]))
    session = new_session()
    open_get_recipe(session)
    session.text_input(key="avoid_pref").set_value("").run()
    assert PantryStore().get_preferences("default").dietary_restrictions == []


def test_hard_filters_survive_leaving_the_page():
    """Regression: Streamlit dropped these widget keys off screen, so they reset to defaults."""
    session = new_session()
    open_get_recipe(session)
    session.selectbox(key="diet_pref").set_value("Vegan").run()
    session.text_input(key="avoid_pref").set_value("peanuts").run()

    for label in ("Home", "Evaluation Plan", "My Inventory"):
        click(session, label)
        assert session.session_state["diet_pref"] == "Vegan"
        assert session.session_state["avoid_pref"] == "peanuts"

    click(session, "Get Recipe")
    assert session.selectbox(key="diet_pref").value == "Vegan"
    assert session.text_input(key="avoid_pref").value == "peanuts"


def test_hard_filters_still_apply_after_ranking_and_more_clicks():
    session = new_session()
    open_get_recipe(session)
    session.selectbox(key="diet_pref").set_value("Vegan").run()
    session.text_input(key="avoid_pref").set_value("peanuts").run()
    click(session, "My Inventory")
    click(session, "Confirm Inventory")
    click(session, "Get Recipe")
    click(session, "Rank My Recipes")
    assert session.session_state["page"] == "Recommendations"

    session.run()
    session.run()
    assert session.session_state["diet_pref"] == "Vegan"
    assert session.session_state["avoid_pref"] == "peanuts"


def test_chat_refinements_stay_temporary():
    """"Make it faster" reorders this list. It must not become a saved preference."""
    session = new_session()
    session.session_state["priority_pref"] = "Fastest"
    session.run()
    assert PantryStore().get_preferences("default").priority == "Best pantry match"
    assert new_session().session_state["priority_pref"] == "Best pantry match"


def test_changing_one_preference_does_not_save_a_refined_one():
    session = new_session()
    open_get_recipe(session)
    session.session_state["priority_pref"] = "Fastest"
    session.selectbox(key="diet_pref").set_value("Vegan").run()
    saved = PantryStore().get_preferences("default")
    assert saved.diet == "Vegan"
    assert saved.priority == "Best pantry match"


# ---------- Profiles ----------
def test_profiles_keep_separate_pantries_and_preferences():
    first = new_session()
    open_get_recipe(first)
    first.selectbox(key="diet_pref").set_value("Vegan").run()

    PantryStore().ensure_user("bob", seed_items=[PantryItemCreate(name="Steak", quantity=1, unit="count")])

    bob = new_session(profile="bob")
    assert pantry_names(bob) == {"Steak"}
    assert bob.session_state["diet_pref"] == "Vegetarian"
    assert new_session().session_state["diet_pref"] == "Vegan"


def test_url_keeps_a_refresh_on_the_same_profile():
    PantryStore().ensure_user("aditya", seed_items=[PantryItemCreate(name="Tofu", quantity=1, unit="block")])
    session = new_session(profile="Aditya")
    assert session.session_state["profile"] == "aditya"
    assert pantry_names(session) == {"Tofu"}


def test_bad_profile_in_the_url_falls_back_to_the_default():
    assert new_session(profile="../../etc").session_state["profile"] == "default"


def test_switching_profile_leaves_nothing_from_the_old_one():
    session = new_session()
    click(session, "My Inventory")
    click(session, "Confirm Inventory")
    session.session_state["review_items"] = [{"Ingredient": "Secret", "Quantity": 1, "Unit": "cup"}]
    session.text_input(key="gemini_api_key_input").set_value(SESSION_ONLY_KEY).run()

    session.text_input(key="profile_input").set_value("Second Person").run()
    assert not session.exception

    assert session.session_state["profile"] == "second person"
    assert session.query_params["profile"] == "second person"
    assert session.session_state["page"] == "Home"
    assert session.session_state["confirmed"] is False
    assert session.session_state["review_items"] == []
    # A new profile starts from the same documented state as a first visit.
    assert pantry_names(session) == STARTER_NAMES
    # The key belongs to this browser session, not to the profile.
    assert session.session_state["gemini_api_key"] == SESSION_ONLY_KEY


def test_invalid_profile_name_is_refused_and_keeps_the_current_one():
    session = new_session()
    session.text_input(key="profile_input").set_value("bad/name").run()
    assert not session.exception
    assert session.session_state["profile"] == "default"
    assert session.text_input(key="profile_input").value == "default"
    assert any("Profile names" in error.value for error in session.error)


# ---------- UI and API share one database ----------
def test_ui_and_api_see_each_others_writes():
    session = new_session()
    api = TestClient(api_app)

    names = {item["name"] for item in api.get("/api/v1/users/default/pantry").json()}
    assert names == STARTER_NAMES

    open_get_recipe(session)
    session.selectbox(key="cuisine_pref").set_value("Asian").run()
    assert api.get("/api/v1/users/default/preferences").json()["cuisine"] == "Asian"

    api.post("/api/v1/users/default/pantry", json={"name": "Tofu", "quantity": 1, "unit": "block"})
    api.patch("/api/v1/users/default/preferences", json={"diet": "Vegan", "max_minutes": None})
    returning = new_session()
    assert "Tofu" in pantry_names(returning)
    assert returning.session_state["diet_pref"] == "Vegan"
    assert returning.session_state["max_time_pref"] == "No limit"


def test_every_preference_the_api_accepts_can_be_shown_by_the_ui():
    """A value missing from a select box would crash the Get Recipe page."""
    api = TestClient(api_app)
    api.put("/api/v1/users/default")
    for field, choices in {
        "diet": ["No preference", "Vegetarian", "Vegan"],
        "cuisine": ["Any", "Indian", "Mediterranean", "Asian"],
        "priority": ["Best pantry match", "Fastest", "Highest protein", "Fewest missing ingredients"],
        "max_minutes": [15, 20, 30, 45, None],
    }.items():
        for choice in choices:
            assert api.patch("/api/v1/users/default/preferences", json={field: choice}).status_code == 200
            session = new_session()
            open_get_recipe(session)
            assert not session.exception


# ---------- Secrets ----------
def test_api_keys_are_never_written_to_the_database(isolated_database):
    session = new_session()
    click(session, "My Inventory")
    session.text_input(key="gemini_api_key_input").set_value(SESSION_ONLY_KEY).run()
    session.text_input(key="groq_api_key_input").set_value(SESSION_ONLY_KEY).run()
    click(session, "Confirm Inventory")
    click(session, "Save pantry edits")
    click(session, "Get Recipe")
    session.selectbox(key="diet_pref").set_value("Vegan").run()

    files = [path for path in isolated_database.parent.iterdir() if path.name.startswith(isolated_database.name)]
    assert files
    for path in files:
        assert SESSION_ONLY_KEY.encode() not in path.read_bytes(), path.name


# ---------- Failures ----------
def test_unusable_database_shows_an_error_instead_of_crashing(tmp_path, monkeypatch):
    blocker = tmp_path / "not-a-folder"
    blocker.write_text("")
    monkeypatch.setenv("CHEFNOVA_DB_PATH", str(blocker / "chefnova.db"))
    session = AppTest.from_file(APP_FILE, default_timeout=30).run()
    assert not session.exception
    assert any("could not open its saved pantry" in error.value for error in session.error)


def test_recipe_details_show_verified_amounts_and_unknown_quantities():
    session = new_session()
    session.session_state["page"] = "Recipe Details"
    recipe = {"title": "Rice bowl", "ingredients": ["Rice"], "time": 15, "diet": "Vegan",
              "ingredient_amounts": {"rice": (1, "cup")}}
    session.session_state["selected_recipe"] = {"recipe": recipe}
    session.run()
    assert not session.exception
    assert any("Rice (1 cup)" in item.value for item in session.markdown)
    assert any("Cook now" in item.value for item in session.success)

    session.session_state["selected_recipe"] = {"recipe": {**recipe, "ingredient_amounts": {}}}
    session.run()
    assert not session.exception
    assert any("Check amounts: Rice" in item.value for item in session.warning)
