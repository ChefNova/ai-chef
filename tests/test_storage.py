"""Database rules, checked against a real SQLite file."""

import shutil
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from pydantic import ValidationError

import app.storage as storage
from app.storage import (
    DEFAULT_DB_PATH,
    MIGRATIONS,
    DuplicateItemError,
    ItemNotFoundError,
    PantryStore,
    StorageError,
    UserNotFoundError,
    resolve_db_path,
)
from app.storage_models import DEFAULT_PREFERENCES, PantryItemCreate, PantryItemUpdate, PreferencesUpdate

REPO_ROOT = Path(__file__).resolve().parent.parent


def item(name="Rice", quantity=2, unit="cups"):
    return PantryItemCreate(name=name, quantity=quantity, unit=unit)


def as_tuples(items):
    return [(entry.name, entry.quantity, entry.unit) for entry in items]


@pytest.fixture
def user(store):
    store.ensure_user("aditya")
    return "aditya"


# ---------- Schema ----------
def test_new_database_is_at_the_latest_schema_version(store):
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == len(MIGRATIONS)
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"users", "pantry_items", "user_preferences", "dietary_restrictions"} <= tables


def test_reopening_keeps_data_and_does_not_rerun_migrations(store, user):
    store.add_item(user, item())
    reopened = PantryStore(store.path)
    assert as_tuples(reopened.list_pantry(user)) == [("Rice", 2.0, "cups")]


def test_database_from_newer_code_is_refused_and_left_alone(store, user):
    store.add_item(user, item())
    with sqlite3.connect(store.path) as conn:
        conn.execute(f"PRAGMA user_version = {len(MIGRATIONS) + 1}")
    with pytest.raises(StorageError, match="schema version"):
        PantryStore(store.path)
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT count(*) FROM pantry_items").fetchone()[0] == 1


def test_failed_migration_rolls_back_completely(tmp_path, monkeypatch):
    path = tmp_path / "broken.db"
    broken = ("CREATE TABLE half_done (id INTEGER PRIMARY KEY)", "THIS IS NOT SQL")
    monkeypatch.setattr(storage, "MIGRATIONS", (broken,))
    with pytest.raises(sqlite3.OperationalError):
        PantryStore(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM sqlite_master WHERE name = 'half_done'").fetchone()[0] == 0


def test_database_rejects_bad_rows_even_without_the_models(store, user):
    with sqlite3.connect(store.path) as conn:
        user_id = conn.execute("SELECT id FROM users").fetchone()[0]
        insert = (
            "INSERT INTO pantry_items (user_id, name, normalized_name, quantity, unit, normalized_unit) "
            "VALUES (?, 'x', 'x', ?, 'u', 'u')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(insert, (user_id, -1))
        with pytest.raises(sqlite3.Error):
            conn.execute(insert, (user_id, "lots"))
        conn.execute(insert, (user_id, 1))
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(insert, (user_id, 1))


def test_foreign_keys_are_enforced_on_store_connections(store):
    with store._transaction(write=True) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO pantry_items (user_id, name, normalized_name, quantity, unit, normalized_unit) "
                "VALUES (9999, 'x', 'x', 1, 'u', 'u')"
            )


def test_failed_write_rolls_back_the_whole_transaction(store, user):
    with pytest.raises(RuntimeError):
        with store._transaction(write=True) as conn:
            conn.execute(
                "INSERT INTO pantry_items (user_id, name, normalized_name, quantity, unit, normalized_unit) "
                "VALUES (1, 'x', 'x', 1, 'u', 'u')"
            )
            raise RuntimeError("boom")
    assert store.list_pantry(user) == []


# ---------- Database location ----------
def test_default_path_does_not_depend_on_the_working_directory(monkeypatch, tmp_path):
    monkeypatch.delenv("CHEFNOVA_DB_PATH")
    monkeypatch.chdir(tmp_path)
    assert resolve_db_path() == DEFAULT_DB_PATH
    assert DEFAULT_DB_PATH == REPO_ROOT / "data" / "chefnova.db"


def test_database_file_is_ignored_by_git():
    if not (REPO_ROOT / ".git").exists() or shutil.which("git") is None:
        pytest.skip("Needs a git checkout, and this copy is not one.")
    for name in ("data/chefnova.db", "data/chefnova.db-wal", "data/chefnova.db-shm"):
        result = subprocess.run(["git", "check-ignore", "-q", name], cwd=REPO_ROOT)
        assert result.returncode == 0, f"{name} could be committed"


def test_missing_parent_folders_are_created(tmp_path):
    store = PantryStore(tmp_path / "does" / "not" / "exist" / "yet.db")
    assert store.path.exists()


# ---------- Persistence ----------
def test_data_survives_a_separate_process(store, user):
    """A real restart: another Python process writes, and this one reads what it left on disk."""
    script = (
        "from app.storage import PantryStore\n"
        "from app.storage_models import PantryItemCreate, PreferencesUpdate\n"
        "store = PantryStore()\n"
        "store.add_item('aditya', PantryItemCreate(name='Lentils', quantity=3, unit='cups'))\n"
        "store.update_preferences('aditya', PreferencesUpdate(diet='Vegan', dietary_restrictions=['peanuts']))\n"
    )
    subprocess.run([sys.executable, "-c", script], cwd=REPO_ROOT, check=True)

    assert as_tuples(store.list_pantry(user)) == [("Lentils", 3.0, "cups")]
    preferences = store.get_preferences(user)
    assert preferences.diet == "Vegan"
    assert preferences.dietary_restrictions == ["peanuts"]


def test_concurrent_writers_lose_no_updates(store, user):
    errors = []

    def add_many():
        try:
            for _ in range(25):
                PantryStore(store.path).add_item(user, item(quantity=1))
        except Exception as exc:  # noqa: BLE001 - reported by the assert below
            errors.append(exc)

    threads = [threading.Thread(target=add_many) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert as_tuples(store.list_pantry(user)) == [("Rice", 200.0, "cups")]


# ---------- Profiles ----------
def test_profile_names_ignore_case_and_extra_spaces(store):
    first, created = store.ensure_user("  Aditya   Dilip ")
    again, created_again = store.ensure_user("aditya dilip")
    assert (created, created_again) == (True, False)
    assert first.id == again.id
    assert first.username == "aditya dilip"


@pytest.mark.parametrize("name", ["", "   ", "a/b", "../etc", "x" * 65, "semi;colon", "-leading"])
def test_unusable_profile_names_are_rejected(store, name):
    with pytest.raises(ValueError):
        store.ensure_user(name)


def test_unknown_profile_is_an_error_and_is_not_created(store):
    with pytest.raises(UserNotFoundError):
        store.list_pantry("ghost")
    with pytest.raises(UserNotFoundError):
        store.add_item("ghost", item())
    with pytest.raises(UserNotFoundError):
        store.get_user("ghost")


def test_new_profile_gets_default_preferences_and_an_empty_pantry(store):
    store.ensure_user("new")
    preferences = store.get_preferences("new")
    assert store.list_pantry("new") == []
    assert preferences.model_dump(exclude={"updated_at", "dietary_restrictions"}) == DEFAULT_PREFERENCES
    assert preferences.dietary_restrictions == []


def test_seed_items_are_only_added_when_the_profile_is_created(store):
    store.ensure_user("seeded", seed_items=[item()])
    store.replace_pantry("seeded", [])
    store.ensure_user("seeded", seed_items=[item()])
    assert store.list_pantry("seeded") == []


def test_deleting_a_profile_erases_everything_it_owned(store, user):
    store.add_item(user, item())
    store.update_preferences(user, PreferencesUpdate(dietary_restrictions=["peanuts"]))
    store.delete_user(user)
    with sqlite3.connect(store.path) as conn:
        for table in ("users", "pantry_items", "user_preferences", "dietary_restrictions"):
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0, table


# ---------- Pantry: add and view ----------
def test_add_returns_the_saved_row(store, user):
    saved, created = store.add_item(user, item("  Greek   Yogurt ", 1, "container"))
    assert created is True
    assert saved.name == "Greek Yogurt"
    assert store.get_item(user, saved.id) == saved


def test_same_name_and_unit_add_together_ignoring_case(store, user):
    first, _ = store.add_item(user, item("Rice", 2, "cups"))
    merged, created = store.add_item(user, item(" RICE ", 1.5, "CUPS"))
    assert created is False
    assert merged.id == first.id
    assert merged.quantity == 3.5
    assert merged.name == "Rice"
    assert len(store.list_pantry(user)) == 1


def test_different_units_stay_on_separate_rows(store, user):
    store.add_item(user, item("Rice", 2, "cups"))
    store.add_item(user, item("Rice", 1, "lb"))
    assert sorted(as_tuples(store.list_pantry(user))) == [("Rice", 1.0, "lb"), ("Rice", 2.0, "cups")]


def test_merging_again_finds_the_right_unit_when_a_name_has_two(store, user):
    """The session-only merge compared one row per name, so this used to add a duplicate."""
    store.add_item(user, item("Rice", 2, "cups"))
    store.add_item(user, item("Rice", 1, "lb"))
    store.add_item(user, item("Rice", 1, "cups"))
    assert sorted(as_tuples(store.list_pantry(user))) == [("Rice", 1.0, "lb"), ("Rice", 3.0, "cups")]


def test_merged_quantities_do_not_pick_up_float_noise(store, user):
    store.add_item(user, item(quantity=0.1))
    merged, _ = store.add_item(user, item(quantity=0.2))
    assert merged.quantity == 0.3


def test_unit_defaults_to_count_when_missing_or_blank(store, user):
    assert PantryItemCreate(name="Eggs", quantity=6).unit == "count"
    assert PantryItemCreate(name="Eggs", quantity=6, unit="   ").unit == "count"


def test_add_many_saves_nothing_if_one_row_fails(store, user):
    class Exploding:
        name = "Boom"
        quantity = 1
        unit = None  # Fails the NOT NULL column after the first row was already written.

    with pytest.raises(sqlite3.IntegrityError):
        store.add_items(user, [item("Rice"), Exploding()])
    assert store.list_pantry(user) == []


def test_pantry_lists_in_alphabetical_order(store, user):
    for name in ("spinach", "Apples", "rice"):
        store.add_item(user, item(name))
    assert [entry.name for entry in store.list_pantry(user)] == ["Apples", "rice", "spinach"]


@pytest.mark.parametrize(
    "fields",
    [
        {"name": "", "quantity": 1},
        {"name": "    ", "quantity": 1},
        {"name": "x" * 121, "quantity": 1},
        {"name": "Rice", "quantity": -1},
        {"name": "Rice", "quantity": float("nan")},
        {"name": "Rice", "quantity": float("inf")},
        {"name": "Rice", "quantity": 1_000_001},
        {"name": "Rice", "quantity": "2"},
        {"name": "Rice", "quantity": True},
        {"name": "Rice"},
        {"name": "Rice", "quantity": 1, "unit": "x" * 41},
        {"name": "Rice", "quantity": 1, "price": 3.99},
    ],
)
def test_invalid_items_are_rejected(fields):
    with pytest.raises(ValidationError):
        PantryItemCreate(**fields)


def test_zero_quantity_is_allowed(store, user):
    saved, _ = store.add_item(user, item(quantity=0))
    assert saved.quantity == 0


# ---------- Pantry: edit ----------
def test_update_changes_only_the_fields_sent(store, user):
    saved, _ = store.add_item(user, item("Rice", 2, "cups"))
    updated = store.update_item(user, saved.id, PantryItemUpdate(quantity=5))
    assert as_tuples([updated]) == [("Rice", 5.0, "cups")]
    assert updated.created_at == saved.created_at
    assert updated.updated_at >= saved.updated_at


def test_renamed_item_is_found_under_its_new_name_when_merging(store, user):
    saved, _ = store.add_item(user, item("Rice", 2, "cups"))
    store.update_item(user, saved.id, PantryItemUpdate(name="Basmati"))
    merged, created = store.add_item(user, item("basmati", 1, "cups"))
    assert created is False
    assert merged.id == saved.id
    assert merged.quantity == 3


def test_update_cannot_collide_with_another_row(store, user):
    store.add_item(user, item("Rice", 2, "cups"))
    other, _ = store.add_item(user, item("Rice", 1, "lb"))
    with pytest.raises(DuplicateItemError):
        store.update_item(user, other.id, PantryItemUpdate(unit="CUPS"))
    assert sorted(as_tuples(store.list_pantry(user))) == [("Rice", 1.0, "lb"), ("Rice", 2.0, "cups")]


def test_update_may_change_only_the_capitalization_of_a_row(store, user):
    saved, _ = store.add_item(user, item("rice", 2, "cups"))
    updated = store.update_item(user, saved.id, PantryItemUpdate(name="Rice"))
    assert updated.name == "Rice"


def test_update_that_changes_nothing_keeps_the_timestamp(store, user):
    saved, _ = store.add_item(user, item())
    same = store.update_item(user, saved.id, PantryItemUpdate(quantity=saved.quantity))
    assert same.updated_at == saved.updated_at


@pytest.mark.parametrize("fields", [{}, {"name": None}, {"quantity": None}, {"unit": None}, {"quantity": -1}, {"id": 2}])
def test_invalid_updates_are_rejected(fields):
    with pytest.raises(ValidationError):
        PantryItemUpdate(**fields)


# ---------- Pantry: delete ----------
def test_delete_removes_only_that_row(store, user):
    first, _ = store.add_item(user, item("Rice"))
    store.add_item(user, item("Beans"))
    store.delete_item(user, first.id)
    assert [entry.name for entry in store.list_pantry(user)] == ["Beans"]
    with pytest.raises(ItemNotFoundError):
        store.delete_item(user, first.id)


def test_deleted_ids_are_never_reused(store, user):
    first, _ = store.add_item(user, item("Rice"))
    store.delete_item(user, first.id)
    second, _ = store.add_item(user, item("Beans"))
    assert second.id != first.id


# ---------- Pantry: replace ----------
def test_replace_adds_changes_and_removes_rows(store, user):
    store.add_items(user, [item("Rice", 2, "cups"), item("Beans", 1, "cans")])
    result = store.replace_pantry(user, [item("Rice", 5, "cups"), item("Tofu", 1, "block")])
    assert as_tuples(result) == [("Rice", 5.0, "cups"), ("Tofu", 1.0, "block")]


def test_replace_keeps_ids_and_timestamps_of_unchanged_rows(store, user):
    rice, _ = store.add_item(user, item("Rice", 2, "cups"))
    beans, _ = store.add_item(user, item("Beans", 1, "cans"))
    result = store.replace_pantry(user, [item("Beans", 1, "cans"), item("Rice", 3, "cups")])
    by_name = {entry.name: entry for entry in result}
    assert by_name["Beans"] == beans
    assert by_name["Rice"].id == rice.id
    assert by_name["Rice"].created_at == rice.created_at


def test_replace_combines_duplicate_rows_instead_of_failing(store, user):
    result = store.replace_pantry(user, [item("Rice", 1, "cups"), item("rice", 2, "CUPS")])
    assert as_tuples(result) == [("Rice", 3.0, "cups")]


def test_replace_with_nothing_empties_the_pantry(store, user):
    store.add_item(user, item())
    assert store.replace_pantry(user, []) == []
    assert store.list_pantry(user) == []


# ---------- Separation between profiles ----------
def test_profiles_cannot_see_or_change_each_others_rows(store, user):
    store.ensure_user("other")
    mine, _ = store.add_item(user, item("Rice", 2, "cups"))
    theirs, _ = store.add_item("other", item("Rice", 9, "cups"))

    assert mine.id != theirs.id
    assert as_tuples(store.list_pantry(user)) == [("Rice", 2.0, "cups")]
    for action in (
        lambda: store.get_item("other", mine.id),
        lambda: store.update_item("other", mine.id, PantryItemUpdate(quantity=0)),
        lambda: store.delete_item("other", mine.id),
    ):
        with pytest.raises(ItemNotFoundError):
            action()
    assert as_tuples(store.list_pantry(user)) == [("Rice", 2.0, "cups")]

    store.replace_pantry("other", [])
    assert as_tuples(store.list_pantry(user)) == [("Rice", 2.0, "cups")]


def test_preferences_are_kept_per_profile(store, user):
    store.ensure_user("other")
    store.update_preferences(user, PreferencesUpdate(diet="Vegan", dietary_restrictions=["peanuts"]))
    other = store.get_preferences("other")
    assert other.diet == DEFAULT_PREFERENCES["diet"]
    assert other.dietary_restrictions == []


# ---------- Preferences ----------
def test_update_changes_only_the_preferences_sent(store, user):
    updated = store.update_preferences(user, PreferencesUpdate(cuisine="Indian"))
    assert updated.cuisine == "Indian"
    assert updated.diet == DEFAULT_PREFERENCES["diet"]
    assert updated.max_minutes == DEFAULT_PREFERENCES["max_minutes"]


def test_no_time_limit_is_saved_as_null(store, user):
    assert store.update_preferences(user, PreferencesUpdate(max_minutes=None)).max_minutes is None
    assert store.get_preferences(user).max_minutes is None


def test_omitting_max_minutes_is_not_the_same_as_clearing_it(store, user):
    store.update_preferences(user, PreferencesUpdate(max_minutes=45))
    assert store.update_preferences(user, PreferencesUpdate(diet="Vegan")).max_minutes == 45


def test_high_protein_is_returned_as_a_boolean(store, user):
    assert store.update_preferences(user, PreferencesUpdate(high_protein=False)).high_protein is False


def test_restrictions_replace_the_saved_list_and_drop_repeats(store, user):
    store.update_preferences(user, PreferencesUpdate(dietary_restrictions=["Peanuts", "peanuts", " shellfish "]))
    assert store.get_preferences(user).dietary_restrictions == ["Peanuts", "shellfish"]
    store.update_preferences(user, PreferencesUpdate(dietary_restrictions=["soy"]))
    assert store.get_preferences(user).dietary_restrictions == ["soy"]


def test_changing_other_preferences_leaves_restrictions_alone(store, user):
    store.update_preferences(user, PreferencesUpdate(dietary_restrictions=["peanuts"]))
    store.update_preferences(user, PreferencesUpdate(diet="Vegan"))
    assert store.get_preferences(user).dietary_restrictions == ["peanuts"]


def test_empty_list_clears_restrictions(store, user):
    store.update_preferences(user, PreferencesUpdate(dietary_restrictions=["peanuts"]))
    store.update_preferences(user, PreferencesUpdate(dietary_restrictions=[]))
    assert store.get_preferences(user).dietary_restrictions == []


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"diet": "Keto"},
        {"diet": None},
        {"cuisine": "Martian"},
        {"priority": "Random"},
        {"max_minutes": 25},
        {"max_minutes": 0},
        {"high_protein": None},
        {"dietary_restrictions": None},
        {"dietary_restrictions": [""]},
        {"dietary_restrictions": ["x" * 81]},
        {"dietary_restrictions": [f"term {index}" for index in range(101)]},
        {"gemini_api_key": "AIza-should-never-be-stored"},
    ],
)
def test_invalid_preference_updates_are_rejected(fields):
    with pytest.raises(ValidationError):
        PreferencesUpdate(**fields)


def test_sql_in_values_is_stored_as_plain_text(store, user):
    nasty = "Robert'); DROP TABLE pantry_items;--"
    saved, _ = store.add_item(user, item(nasty))
    store.update_preferences(user, PreferencesUpdate(dietary_restrictions=[nasty]))
    assert saved.name == nasty
    assert store.get_preferences(user).dietary_restrictions == [nasty]
    assert [entry.name for entry in store.list_pantry(user)] == [nasty]
