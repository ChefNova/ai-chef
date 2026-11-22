"""Username/password accounts. Google accounts are covered in test_ui_persistence.py."""

import sqlite3

import pytest

import app.storage as storage
from app.storage import AccountExistsError, PantryStore, StorageError
from app.storage_models import DEFAULT_PREFERENCES, PantryItemCreate

PASSWORD = "correct horse battery"


def test_new_account_signs_in_with_its_password(store):
    created = store.create_account("Priya", "Priya@example.com", PASSWORD)
    assert created.username == "priya"
    assert store.check_password("PRIYA", PASSWORD) == created


@pytest.mark.parametrize("username, password", [("priya", "wrong password"), ("nobody", PASSWORD), ("bad/name", PASSWORD)])
def test_wrong_password_or_unknown_name_is_refused(store, username, password):
    store.create_account("priya", "priya@example.com", PASSWORD)
    assert store.check_password(username, password) is None


def test_new_account_gets_default_preferences_and_starter_items(store):
    store.create_account("priya", "priya@example.com", PASSWORD, seed_items=[PantryItemCreate(name="Rice", quantity=2, unit="cups")])
    assert [item.name for item in store.list_pantry("priya")] == ["Rice"]
    assert store.get_preferences("priya").diet == DEFAULT_PREFERENCES["diet"]


def test_username_is_taken_once(store):
    store.create_account("priya", "priya@example.com", PASSWORD)
    with pytest.raises(AccountExistsError):
        store.create_account("Priya", "Priya@example.com", "another password")


def test_existing_profile_without_password_cannot_be_claimed_or_entered(store):
    store.ensure_user("aditya")
    with pytest.raises(AccountExistsError):
        store.create_account("aditya", "aditya@example.com", PASSWORD)
    assert store.check_password("aditya", "") is None


def test_password_accounts_cannot_use_google_names(store):
    with pytest.raises(ValueError, match="google-"):
        store.create_account("google-123", "google-123@example.com", PASSWORD)


@pytest.mark.parametrize("password", ["short", "x" * 129])
def test_password_length_is_checked(store, password):
    with pytest.raises(ValueError, match="8-128"):
        store.create_account("priya", "priya@example.com", password)


def test_password_is_stored_only_as_a_salted_hash(store):
    store.create_account("one", "one@example.com", PASSWORD)
    store.create_account("two", "two@example.com", PASSWORD)
    with sqlite3.connect(store.path) as conn:
        hashes = [row[0] for row in conn.execute("SELECT password_hash FROM users ORDER BY username")]
    assert all(h.startswith("scrypt$") and PASSWORD not in h for h in hashes)
    assert hashes[0] != hashes[1]
    # The hash never leaves the store in a User (so the API never returns it).
    assert not {"password_hash", "email"} & store.get_user("one").model_dump().keys()


def test_database_from_before_accounts_is_upgraded_and_keeps_its_data(tmp_path):
    path = tmp_path / "old.db"
    # Build a version-1 database the way the code before accounts did.
    with sqlite3.connect(path) as conn:
        for statement in storage.MIGRATIONS[0]:
            conn.execute(statement)
        conn.execute("PRAGMA user_version = 1")
        conn.execute("INSERT INTO users (id, username) VALUES (1, 'aditya')")
        conn.execute(
            "INSERT INTO pantry_items (user_id, name, normalized_name, quantity, unit, normalized_unit)"
            " VALUES (1, 'Tofu', 'tofu', 1, 'block', 'block')"
        )
    upgraded = PantryStore(path)
    assert [item.name for item in upgraded.list_pantry("aditya")] == ["Tofu"]
    upgraded.create_account("priya", "priya@example.com", PASSWORD)
    assert upgraded.check_password("priya", PASSWORD) is not None


def test_email_is_stored_lowercase_and_used_once(store):
    store.create_account("priya", " Priya@Example.COM ", PASSWORD)
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT email FROM users").fetchone() == ("priya@example.com",)
    with pytest.raises(AccountExistsError, match="email"):
        store.create_account("someone else", "PRIYA@example.com", PASSWORD)


@pytest.mark.parametrize("email", ["", "priya", "priya@", "@example.com", "priya@example", "pri ya@example.com"])
def test_bad_email_is_refused_and_nothing_is_saved(store, email):
    with pytest.raises(ValueError, match="valid email"):
        store.create_account("priya", email, PASSWORD)
    with pytest.raises(StorageError):
        store.get_user("priya")
