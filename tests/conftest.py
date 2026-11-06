import pytest

from app.storage import DEFAULT_DB_PATH, PantryStore


@pytest.fixture(autouse=True, scope="session")
def real_database_is_never_touched():
    """Fail the run if any test escaped its temporary database."""

    def fingerprint():
        return DEFAULT_DB_PATH.stat().st_mtime_ns if DEFAULT_DB_PATH.exists() else None

    before = fingerprint()
    yield
    assert fingerprint() == before, f"A test wrote to the real database at {DEFAULT_DB_PATH}."


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    """Point every test at its own file, so no test can touch a developer's real pantry."""
    path = tmp_path / "chefnova-test.db"
    monkeypatch.setenv("CHEFNOVA_DB_PATH", str(path))
    return path


@pytest.fixture
def store(isolated_database):
    return PantryStore(isolated_database)
