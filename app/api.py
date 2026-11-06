"""REST API for profiles, pantries, and preferences.

Run from the repo root:

    uvicorn app.api:app --reload

Interactive docs are then at http://127.0.0.1:8000/docs.

There is no authentication. A profile name is an identifier, not a login, so keep this
bound to localhost. See docs/ARCHITECTURE.md.
"""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Path, Request, Response, status
from fastapi.responses import JSONResponse

from app.storage import (
    DuplicateItemError,
    ItemNotFoundError,
    PantryStore,
    StorageError,
    UserNotFoundError,
)
from app.storage_models import (
    PantryItem,
    PantryItemCreate,
    PantryItemUpdate,
    Preferences,
    PreferencesUpdate,
    User,
    Username,
)


def get_store() -> PantryStore:
    return PantryStore()


Store = Annotated[PantryStore, Depends(get_store)]
ProfileName = Annotated[Username, Path(description="Profile name. Matching ignores case.")]
ItemId = Annotated[int, Path(ge=1)]

router = APIRouter(prefix="/api/v1")


# ---------- Profiles ----------
@router.put(
    "/users/{username}",
    tags=["profiles"],
    responses={201: {"model": User, "description": "Profile created"}},
)
def create_or_get_user(username: ProfileName, store: Store, response: Response) -> User:
    """Create the profile with default preferences, or return it if it exists."""
    user, created = store.ensure_user(username)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return user


@router.get("/users/{username}", tags=["profiles"])
def get_user(username: ProfileName, store: Store) -> User:
    return store.get_user(username)


@router.delete("/users/{username}", tags=["profiles"], status_code=status.HTTP_204_NO_CONTENT)
def delete_user(username: ProfileName, store: Store) -> None:
    """Erase the profile, its pantry, and its preferences."""
    store.delete_user(username)


# ---------- Pantry ----------
@router.get("/users/{username}/pantry", tags=["pantry"])
def list_pantry(username: ProfileName, store: Store) -> list[PantryItem]:
    return store.list_pantry(username)


@router.post(
    "/users/{username}/pantry",
    tags=["pantry"],
    responses={201: {"model": PantryItem, "description": "New row created"}},
)
def add_item(username: ProfileName, item: PantryItemCreate, store: Store, response: Response) -> PantryItem:
    """Add an item. The same name and unit add to the existing row and return 200."""
    saved, created = store.add_item(username, item)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return saved


@router.put("/users/{username}/pantry", tags=["pantry"])
def replace_pantry(username: ProfileName, items: list[PantryItemCreate], store: Store) -> list[PantryItem]:
    """Make the pantry match this list exactly. An empty list clears it."""
    return store.replace_pantry(username, items)


@router.get("/users/{username}/pantry/{item_id}", tags=["pantry"])
def get_item(username: ProfileName, item_id: ItemId, store: Store) -> PantryItem:
    return store.get_item(username, item_id)


@router.patch("/users/{username}/pantry/{item_id}", tags=["pantry"])
def update_item(username: ProfileName, item_id: ItemId, changes: PantryItemUpdate, store: Store) -> PantryItem:
    """Change a row. Returns 409 if the new name and unit match another row."""
    return store.update_item(username, item_id, changes)


@router.delete("/users/{username}/pantry/{item_id}", tags=["pantry"], status_code=status.HTTP_204_NO_CONTENT)
def delete_item(username: ProfileName, item_id: ItemId, store: Store) -> None:
    store.delete_item(username, item_id)


# ---------- Preferences ----------
@router.get("/users/{username}/preferences", tags=["preferences"])
def get_preferences(username: ProfileName, store: Store) -> Preferences:
    return store.get_preferences(username)


@router.patch("/users/{username}/preferences", tags=["preferences"])
def update_preferences(username: ProfileName, changes: PreferencesUpdate, store: Store) -> Preferences:
    """Change only the fields sent. dietary_restrictions replaces the whole list."""
    return store.update_preferences(username, changes)


# ---------- App ----------
def _error(status_code: int):
    def handler(_: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


def _database_unavailable(_: Request, __: Exception) -> JSONResponse:
    # The SQLite message can include file paths, so it is not sent to the client.
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "The database is unavailable. Nothing was saved."},
    )


app = FastAPI(
    title="ChefNova Storage API",
    version="1.0.0",
    description="Saved pantries and preferences for ChefNova.",
)
app.include_router(router)
app.add_exception_handler(UserNotFoundError, _error(status.HTTP_404_NOT_FOUND))
app.add_exception_handler(ItemNotFoundError, _error(status.HTTP_404_NOT_FOUND))
app.add_exception_handler(DuplicateItemError, _error(status.HTTP_409_CONFLICT))
app.add_exception_handler(StorageError, _error(status.HTTP_503_SERVICE_UNAVAILABLE))
app.add_exception_handler(sqlite3.Error, _database_unavailable)


@app.get("/health", tags=["health"])
def health(store: Store) -> dict[str, str]:
    """Report ok once the database has opened and its schema is current."""
    return {"status": "ok"}
