"""SQLite storage for profiles, pantries, and preferences.

All SQL lives here. Both the FastAPI backend and the Streamlit UI call PantryStore,
so they apply the same rules to the same file. See docs/ARCHITECTURE.md.

Every operation opens its own short-lived connection, so a store can be shared
between threads, and between the UI and API processes.
"""

import os
import sqlite3
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

from app.recipe_recommendations import normalize_name
from app.storage_models import (
    DEFAULT_PREFERENCES,
    PantryItem,
    PantryItemCreate,
    PantryItemUpdate,
    Preferences,
    PreferencesUpdate,
    User,
    normalize_username,
)

_APP_DIR = Path(__file__).resolve().parent

# The UI also loads this file, through the receipt extractor. Loading it here keeps the
# API on the same database when CHEFNOVA_DB_PATH is set in .env.
load_dotenv(_APP_DIR / ".env")

# Anchored to the repo, not the working directory, so the UI and API always find the same file.
DEFAULT_DB_PATH = _APP_DIR.parent / "data" / "chefnova.db"
BUSY_TIMEOUT_SECONDS = 10
_NOW = "strftime('%Y-%m-%dT%H:%M:%fZ', 'now')"


class StorageError(Exception):
    """A storage rule was broken or the database cannot be used."""


class UserNotFoundError(StorageError):
    pass


class ItemNotFoundError(StorageError):
    pass


class DuplicateItemError(StorageError):
    pass


# Each entry upgrades the schema by one version. Add new entries. Never edit one that has
# shipped, because existing databases have already applied it.
MIGRATIONS: tuple[tuple[str, ...], ...] = (
    (
        f"""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT ({_NOW})
        ) STRICT
        """,
        # AUTOINCREMENT keeps a deleted item's id from being reused, so a client
        # holding an old id cannot edit a different ingredient by accident.
        f"""
        CREATE TABLE pantry_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL CHECK (length(name) > 0),
            normalized_name TEXT NOT NULL,
            quantity REAL NOT NULL CHECK (quantity >= 0),
            unit TEXT NOT NULL CHECK (length(unit) > 0),
            normalized_unit TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT ({_NOW}),
            updated_at TEXT NOT NULL DEFAULT ({_NOW}),
            UNIQUE (user_id, normalized_name, normalized_unit)
        ) STRICT
        """,
        f"""
        CREATE TABLE user_preferences (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            diet TEXT NOT NULL,
            cuisine TEXT NOT NULL,
            max_minutes INTEGER CHECK (max_minutes IS NULL OR max_minutes > 0),
            priority TEXT NOT NULL,
            high_protein INTEGER NOT NULL CHECK (high_protein IN (0, 1)),
            updated_at TEXT NOT NULL DEFAULT ({_NOW})
        ) STRICT
        """,
        """
        CREATE TABLE dietary_restrictions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            term TEXT NOT NULL CHECK (length(term) > 0),
            normalized_term TEXT NOT NULL,
            UNIQUE (user_id, normalized_term)
        ) STRICT
        """,
    ),
)


def resolve_db_path() -> Path:
    override = os.getenv("CHEFNOVA_DB_PATH", "").strip()
    return Path(override).expanduser().resolve() if override else DEFAULT_DB_PATH


class PantryStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else resolve_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    # ---------- Connections ----------
    @contextmanager
    def _transaction(self, write: bool = False) -> Iterator[sqlite3.Connection]:
        """One transaction on a new connection. Commits on success and rolls back on error.

        Writers take the write lock up front, so a read-then-write inside the block
        cannot race another writer.
        """
        conn = sqlite3.connect(self.path, timeout=BUSY_TIMEOUT_SECONDS, isolation_level=None)
        try:
            conn.row_factory = sqlite3.Row
            # SQLite does not keep this setting between connections.
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            try:
                yield conn
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")
        finally:
            conn.close()

    def _migrate(self) -> None:
        latest = len(MIGRATIONS)
        conn = sqlite3.connect(self.path, timeout=BUSY_TIMEOUT_SECONDS, isolation_level=None)
        try:
            self._enable_wal(conn)
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version == latest:
                return
            if version > latest:
                raise StorageError(
                    f"{self.path} uses schema version {version}, but this code only knows {latest}. "
                    "Update the code, or set CHEFNOVA_DB_PATH to a different file."
                )
            conn.execute("BEGIN IMMEDIATE")
            try:
                # Another process may have migrated while this one waited for the lock.
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                for number, statements in enumerate(MIGRATIONS[version:], start=version + 1):
                    for statement in statements:
                        conn.execute(statement)
                    conn.execute(f"PRAGMA user_version = {number}")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
            conn.execute("COMMIT")
        finally:
            conn.close()

    @staticmethod
    def _enable_wal(conn: sqlite3.Connection) -> None:
        """WAL lets the UI read while the API writes. It only improves concurrency, so a failed switch is not fatal."""
        try:
            if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() != "wal":
                conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError:
            pass

    # ---------- Profiles ----------
    def ensure_user(self, username: str, seed_items: Iterable[PantryItemCreate] = ()) -> tuple[User, bool]:
        """Return (user, created). seed_items are added only when the profile is new.

        Seeding is tied to profile creation, not to an empty pantry, so a user who
        deletes every item does not get the starter rows back.
        """
        name = normalize_username(username)
        with self._transaction() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (name,)).fetchone()
        if row is not None:
            return User.model_validate(dict(row)), False

        with self._transaction(write=True) as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (name,)).fetchone()
            if row is not None:
                return User.model_validate(dict(row)), False
            user_id = conn.execute("INSERT INTO users (username) VALUES (?)", (name,)).lastrowid
            conn.execute(
                """
                INSERT INTO user_preferences (user_id, diet, cuisine, max_minutes, priority, high_protein)
                VALUES (:user_id, :diet, :cuisine, :max_minutes, :priority, :high_protein)
                """,
                {"user_id": user_id, **DEFAULT_PREFERENCES},
            )
            for item in seed_items:
                self._add_or_merge(conn, user_id, item)
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return User.model_validate(dict(row)), True

    def get_user(self, username: str) -> User:
        with self._transaction() as conn:
            user_id = self._user_id(conn, username)
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return User.model_validate(dict(row))

    def delete_user(self, username: str) -> None:
        """Erase a profile. Its pantry, preferences, and restrictions cascade."""
        with self._transaction(write=True) as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (self._user_id(conn, username),))

    # ---------- Pantry ----------
    def list_pantry(self, username: str) -> list[PantryItem]:
        with self._transaction() as conn:
            return self._list_pantry(conn, self._user_id(conn, username))

    def get_item(self, username: str, item_id: int) -> PantryItem:
        with self._transaction() as conn:
            return self._require_item(conn, self._user_id(conn, username), item_id)

    def add_item(self, username: str, item: PantryItemCreate) -> tuple[PantryItem, bool]:
        """Return (item, created). The same name and unit add to the existing row."""
        with self._transaction(write=True) as conn:
            return self._add_or_merge(conn, self._user_id(conn, username), item)

    def add_items(self, username: str, items: Iterable[PantryItemCreate]) -> list[PantryItem]:
        """Add several items in one transaction. If one fails, none are saved."""
        with self._transaction(write=True) as conn:
            user_id = self._user_id(conn, username)
            return [self._add_or_merge(conn, user_id, item)[0] for item in items]

    def update_item(self, username: str, item_id: int, changes: PantryItemUpdate) -> PantryItem:
        with self._transaction(write=True) as conn:
            user_id = self._user_id(conn, username)
            current = self._require_item(conn, user_id, item_id)
            fields = changes.model_dump(exclude_unset=True)
            name = fields.get("name", current.name)
            quantity = fields.get("quantity", current.quantity)
            unit = fields.get("unit", current.unit)
            if (name, quantity, unit) == (current.name, current.quantity, current.unit):
                return current

            clash = conn.execute(
                """
                SELECT id FROM pantry_items
                WHERE user_id = ? AND normalized_name = ? AND normalized_unit = ? AND id != ?
                """,
                (user_id, normalize_name(name), normalize_name(unit), item_id),
            ).fetchone()
            if clash is not None:
                raise DuplicateItemError(
                    f"The pantry already has {name} measured in {unit} (item {clash['id']}). "
                    "Change that item instead, or delete one of them."
                )
            conn.execute(
                f"""
                UPDATE pantry_items
                SET name = ?, normalized_name = ?, quantity = ?, unit = ?, normalized_unit = ?, updated_at = {_NOW}
                WHERE id = ?
                """,
                (name, normalize_name(name), quantity, unit, normalize_name(unit), item_id),
            )
            return self._require_item(conn, user_id, item_id)

    def delete_item(self, username: str, item_id: int) -> None:
        with self._transaction(write=True) as conn:
            user_id = self._user_id(conn, username)
            self._require_item(conn, user_id, item_id)
            conn.execute("DELETE FROM pantry_items WHERE id = ?", (item_id,))

    def replace_pantry(self, username: str, items: Iterable[PantryItemCreate]) -> list[PantryItem]:
        """Make the pantry match items exactly, in one transaction.

        Rows in items that share a name and unit are added together. A row that is
        kept keeps its id and created_at, so only real changes touch the database.
        """
        wanted: dict[tuple[str, str], PantryItemCreate] = {}
        for item in items:
            key = (normalize_name(item.name), normalize_name(item.unit))
            if key in wanted:
                total = round(wanted[key].quantity + item.quantity, 6)
                wanted[key] = wanted[key].model_copy(update={"quantity": total})
            else:
                wanted[key] = item

        with self._transaction(write=True) as conn:
            user_id = self._user_id(conn, username)
            existing = {
                (row["normalized_name"], row["normalized_unit"]): row
                for row in conn.execute("SELECT * FROM pantry_items WHERE user_id = ?", (user_id,))
            }
            for key, row in existing.items():
                if key not in wanted:
                    conn.execute("DELETE FROM pantry_items WHERE id = ?", (row["id"],))
            for key, item in wanted.items():
                row = existing.get(key)
                if row is None:
                    self._insert_item(conn, user_id, item)
                elif (row["name"], row["quantity"], row["unit"]) != (item.name, item.quantity, item.unit):
                    conn.execute(
                        f"UPDATE pantry_items SET name = ?, quantity = ?, unit = ?, updated_at = {_NOW} WHERE id = ?",
                        (item.name, item.quantity, item.unit, row["id"]),
                    )
            return self._list_pantry(conn, user_id)

    # ---------- Preferences ----------
    def get_preferences(self, username: str) -> Preferences:
        with self._transaction() as conn:
            return self._read_preferences(conn, self._user_id(conn, username))

    def update_preferences(self, username: str, changes: PreferencesUpdate) -> Preferences:
        fields = changes.model_dump(exclude_unset=True)
        restrictions = fields.pop("dietary_restrictions", None)
        with self._transaction(write=True) as conn:
            user_id = self._user_id(conn, username)
            if fields:
                # Column names come from the model's fixed field list, never from the request.
                assignments = ", ".join(f"{column} = :{column}" for column in fields)
                conn.execute(
                    f"UPDATE user_preferences SET {assignments}, updated_at = {_NOW} WHERE user_id = :user_id",
                    {**fields, "user_id": user_id},
                )
            if restrictions is not None:
                conn.execute("DELETE FROM dietary_restrictions WHERE user_id = ?", (user_id,))
                conn.executemany(
                    """
                    INSERT INTO dietary_restrictions (user_id, term, normalized_term) VALUES (?, ?, ?)
                    ON CONFLICT (user_id, normalized_term) DO NOTHING
                    """,
                    [(user_id, term, normalize_name(term)) for term in restrictions],
                )
                conn.execute(f"UPDATE user_preferences SET updated_at = {_NOW} WHERE user_id = ?", (user_id,))
            return self._read_preferences(conn, user_id)

    # ---------- Helpers that run inside an open transaction ----------
    @staticmethod
    def _user_id(conn: sqlite3.Connection, username: str) -> int:
        name = normalize_username(username)
        row = conn.execute("SELECT id FROM users WHERE username = ?", (name,)).fetchone()
        if row is None:
            raise UserNotFoundError(f"No profile named '{name}'.")
        return row["id"]

    @staticmethod
    def _list_pantry(conn: sqlite3.Connection, user_id: int) -> list[PantryItem]:
        rows = conn.execute(
            "SELECT * FROM pantry_items WHERE user_id = ? ORDER BY normalized_name, normalized_unit",
            (user_id,),
        ).fetchall()
        return [PantryItem.model_validate(dict(row)) for row in rows]

    @staticmethod
    def _require_item(conn: sqlite3.Connection, user_id: int, item_id: int) -> PantryItem:
        # Filtering on user_id keeps one profile from reaching another profile's rows by id.
        row = conn.execute(
            "SELECT * FROM pantry_items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        ).fetchone()
        if row is None:
            raise ItemNotFoundError(f"No pantry item with id {item_id}.")
        return PantryItem.model_validate(dict(row))

    @staticmethod
    def _insert_item(conn: sqlite3.Connection, user_id: int, item: PantryItemCreate) -> int:
        return conn.execute(
            """
            INSERT INTO pantry_items (user_id, name, normalized_name, quantity, unit, normalized_unit)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, item.name, normalize_name(item.name), item.quantity, item.unit, normalize_name(item.unit)),
        ).lastrowid

    def _add_or_merge(self, conn: sqlite3.Connection, user_id: int, item: PantryItemCreate) -> tuple[PantryItem, bool]:
        row = conn.execute(
            "SELECT id FROM pantry_items WHERE user_id = ? AND normalized_name = ? AND normalized_unit = ?",
            (user_id, normalize_name(item.name), normalize_name(item.unit)),
        ).fetchone()
        if row is None:
            item_id = self._insert_item(conn, user_id, item)
            return self._require_item(conn, user_id, item_id), True
        # ROUND keeps binary float noise out of the table, such as 0.1 + 0.2 = 0.30000000000000004.
        conn.execute(
            f"UPDATE pantry_items SET quantity = ROUND(quantity + ?, 6), updated_at = {_NOW} WHERE id = ?",
            (item.quantity, row["id"]),
        )
        return self._require_item(conn, user_id, row["id"]), False

    @staticmethod
    def _read_preferences(conn: sqlite3.Connection, user_id: int) -> Preferences:
        row = conn.execute("SELECT * FROM user_preferences WHERE user_id = ?", (user_id,)).fetchone()
        terms = conn.execute(
            "SELECT term FROM dietary_restrictions WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
        return Preferences.model_validate({**dict(row), "dietary_restrictions": [term["term"] for term in terms]})
