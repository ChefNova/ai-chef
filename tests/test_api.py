"""HTTP behavior of the storage API: routes, status codes, and error bodies."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.api import app, get_store
from app.storage_models import DEFAULT_PREFERENCES

USER = "/api/v1/users/aditya"
PANTRY = f"{USER}/pantry"
PREFERENCES = f"{USER}/preferences"
RICE = {"name": "Rice", "quantity": 2, "unit": "cups"}


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def profile(client):
    assert client.put(USER).status_code == 201


# ---------- Health and docs ----------
def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_every_route_is_in_the_openapi_document(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths[PANTRY.replace("aditya", "{username}")]) == {"get", "post", "put"}
    assert set(paths[f"{PANTRY}/{{item_id}}".replace("aditya", "{username}")]) == {"get", "patch", "delete"}
    assert set(paths[PREFERENCES.replace("aditya", "{username}")]) == {"get", "patch"}
    assert set(paths[USER.replace("aditya", "{username}")]) == {"put", "get", "delete"}


# ---------- Profiles ----------
def test_put_creates_a_profile_once(client):
    created = client.put(USER)
    again = client.put(USER)
    assert (created.status_code, again.status_code) == (201, 200)
    assert created.json() == again.json()
    assert created.json()["username"] == "aditya"


def test_profile_names_in_urls_ignore_case(client, profile):
    assert client.get("/api/v1/users/ADITYA").json()["username"] == "aditya"


def test_unknown_profile_returns_404_on_every_route(client):
    ghost = "/api/v1/users/ghost"
    responses = [
        client.get(ghost),
        client.delete(ghost),
        client.get(f"{ghost}/pantry"),
        client.post(f"{ghost}/pantry", json=RICE),
        client.put(f"{ghost}/pantry", json=[]),
        client.get(f"{ghost}/pantry/1"),
        client.patch(f"{ghost}/pantry/1", json={"quantity": 1}),
        client.delete(f"{ghost}/pantry/1"),
        client.get(f"{ghost}/preferences"),
        client.patch(f"{ghost}/preferences", json={"diet": "Vegan"}),
    ]
    assert [response.status_code for response in responses] == [404] * len(responses)
    assert "ghost" in responses[0].json()["detail"]
    assert client.get(ghost).status_code == 404


def test_unusable_profile_name_returns_422(client):
    assert client.put("/api/v1/users/bad$name").status_code == 422


def test_delete_profile_erases_its_data(client, profile):
    client.post(PANTRY, json=RICE)
    assert client.delete(USER).status_code == 204
    assert client.get(PANTRY).status_code == 404
    assert client.put(USER).status_code == 201
    assert client.get(PANTRY).json() == []


# ---------- Pantry CRUD ----------
def test_full_pantry_lifecycle(client, profile):
    created = client.post(PANTRY, json=RICE)
    assert created.status_code == 201
    item = created.json()
    assert item["name"] == "Rice"
    assert item["quantity"] == 2
    assert item["unit"] == "cups"

    url = f"{PANTRY}/{item['id']}"
    assert client.get(url).json() == item
    assert client.get(PANTRY).json() == [item]

    edited = client.patch(url, json={"quantity": 3.5, "name": "Brown Rice"})
    assert edited.status_code == 200
    assert (edited.json()["quantity"], edited.json()["name"]) == (3.5, "Brown Rice")
    assert client.get(url).json() == edited.json()

    deleted = client.delete(url)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(url).status_code == 404
    assert client.get(PANTRY).json() == []


def test_post_with_same_name_and_unit_merges_and_returns_200(client, profile):
    first = client.post(PANTRY, json=RICE).json()
    merged = client.post(PANTRY, json={"name": "rice", "quantity": 1, "unit": "CUPS"})
    assert merged.status_code == 200
    assert merged.json()["id"] == first["id"]
    assert merged.json()["quantity"] == 3
    assert len(client.get(PANTRY).json()) == 1


def test_post_with_a_different_unit_makes_a_new_row(client, profile):
    client.post(PANTRY, json=RICE)
    response = client.post(PANTRY, json={"name": "Rice", "quantity": 1, "unit": "lb"})
    assert response.status_code == 201
    assert len(client.get(PANTRY).json()) == 2


def test_patch_into_an_existing_row_returns_409_and_changes_nothing(client, profile):
    client.post(PANTRY, json=RICE)
    other = client.post(PANTRY, json={"name": "Rice", "quantity": 1, "unit": "lb"}).json()
    response = client.patch(f"{PANTRY}/{other['id']}", json={"unit": "cups"})
    assert response.status_code == 409
    assert "already has" in response.json()["detail"]
    assert client.get(f"{PANTRY}/{other['id']}").json() == other


def test_put_replaces_the_whole_pantry(client, profile):
    client.post(PANTRY, json=RICE)
    client.post(PANTRY, json={"name": "Beans", "quantity": 1, "unit": "cans"})
    response = client.put(PANTRY, json=[{"name": "Tofu", "quantity": 1, "unit": "block"}])
    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["Tofu"]
    assert client.get(PANTRY).json() == response.json()
    assert client.put(PANTRY, json=[]).json() == []


def test_put_saves_nothing_if_one_row_is_invalid(client, profile):
    client.post(PANTRY, json=RICE)
    response = client.put(PANTRY, json=[{"name": "Tofu", "quantity": 1}, {"name": "Bad", "quantity": -1}])
    assert response.status_code == 422
    assert [item["name"] for item in client.get(PANTRY).json()] == ["Rice"]


def test_missing_item_returns_404(client, profile):
    assert client.get(f"{PANTRY}/999").status_code == 404
    assert client.patch(f"{PANTRY}/999", json={"quantity": 1}).status_code == 404
    assert client.delete(f"{PANTRY}/999").status_code == 404


def test_item_id_must_be_a_positive_integer(client, profile):
    assert client.get(f"{PANTRY}/0").status_code == 422
    assert client.get(f"{PANTRY}/abc").status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"quantity": 1},
        {"name": "Rice"},
        {"name": "", "quantity": 1},
        {"name": "Rice", "quantity": -1},
        {"name": "Rice", "quantity": "two"},
        {"name": "Rice", "quantity": 1, "user_id": 2},
    ],
)
def test_invalid_item_body_returns_422(client, profile, body):
    assert client.post(PANTRY, json=body).status_code == 422
    assert client.get(PANTRY).json() == []


@pytest.mark.parametrize("body", [{}, {"quantity": None}, {"name": ""}, {"quantity": -1}, {"created_at": "now"}])
def test_invalid_patch_body_returns_422(client, profile, body):
    item = client.post(PANTRY, json=RICE).json()
    assert client.patch(f"{PANTRY}/{item['id']}", json=body).status_code == 422
    assert client.get(f"{PANTRY}/{item['id']}").json() == item


def test_one_profile_cannot_reach_another_profiles_item(client, profile):
    item = client.post(PANTRY, json=RICE).json()
    other = "/api/v1/users/other/pantry"
    client.put("/api/v1/users/other")
    assert client.get(f"{other}/{item['id']}").status_code == 404
    assert client.patch(f"{other}/{item['id']}", json={"quantity": 0}).status_code == 404
    assert client.delete(f"{other}/{item['id']}").status_code == 404
    assert client.get(f"{PANTRY}/{item['id']}").json() == item


def test_internal_columns_are_not_exposed(client, profile):
    item = client.post(PANTRY, json=RICE).json()
    assert set(item) == {"id", "name", "quantity", "unit", "created_at", "updated_at"}


# ---------- Preferences ----------
def test_new_profile_returns_default_preferences(client, profile):
    body = client.get(PREFERENCES).json()
    assert body.pop("updated_at")
    assert body == {**DEFAULT_PREFERENCES, "dietary_restrictions": []}


def test_patch_saves_preferences_restrictions_and_cuisine(client, profile):
    response = client.patch(
        PREFERENCES,
        json={
            "diet": "Vegan",
            "cuisine": "Indian",
            "max_minutes": 45,
            "priority": "Fastest",
            "high_protein": False,
            "dietary_restrictions": ["peanuts", "shellfish"],
        },
    )
    assert response.status_code == 200
    saved = client.get(PREFERENCES).json()
    assert saved == response.json()
    assert saved["diet"] == "Vegan"
    assert saved["cuisine"] == "Indian"
    assert saved["max_minutes"] == 45
    assert saved["priority"] == "Fastest"
    assert saved["high_protein"] is False
    assert saved["dietary_restrictions"] == ["peanuts", "shellfish"]


def test_patch_leaves_other_fields_alone(client, profile):
    client.patch(PREFERENCES, json={"diet": "Vegan", "dietary_restrictions": ["peanuts"]})
    saved = client.patch(PREFERENCES, json={"cuisine": "Asian"}).json()
    assert saved["diet"] == "Vegan"
    assert saved["dietary_restrictions"] == ["peanuts"]


def test_null_max_minutes_means_no_limit(client, profile):
    assert client.patch(PREFERENCES, json={"max_minutes": None}).json()["max_minutes"] is None


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"diet": "Keto"},
        {"diet": None},
        {"cuisine": "Martian"},
        {"max_minutes": 25},
        {"dietary_restrictions": [""]},
        {"gemini_api_key": "AIza-should-never-be-stored"},
    ],
)
def test_invalid_preferences_return_422_and_change_nothing(client, profile, body):
    before = client.get(PREFERENCES).json()
    assert client.patch(PREFERENCES, json=body).status_code == 422
    assert client.get(PREFERENCES).json() == before


# ---------- Persistence and failures ----------
def test_data_survives_a_new_client_and_new_store(client, profile):
    client.post(PANTRY, json=RICE)
    client.patch(PREFERENCES, json={"diet": "Vegan"})
    with TestClient(app) as restarted:
        assert [item["name"] for item in restarted.get(PANTRY).json()] == ["Rice"]
        assert restarted.get(PREFERENCES).json()["diet"] == "Vegan"


def test_database_failure_returns_503_without_leaking_details(client):
    class BrokenStore:
        def list_pantry(self, username):
            raise sqlite3.OperationalError("unable to open /secret/path/chefnova.db")

    app.dependency_overrides[get_store] = BrokenStore
    try:
        response = client.get(PANTRY)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert "secret" not in response.text
