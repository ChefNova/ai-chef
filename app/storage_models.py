"""Data shapes for saved pantries and preferences.

The store, the API, and the Streamlit UI all validate against these models and
read their choices from the constants below. A value the API accepts can always
be shown by the UI's select boxes, because both use the same list.
"""

import re
from typing import Annotated, Literal, get_args

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

Diet = Literal["No preference", "Vegetarian", "Vegan"]
Cuisine = Literal["Any", "Indian", "Mediterranean", "Asian"]
Priority = Literal["Best pantry match", "Fastest", "Highest protein", "Fewest missing ingredients"]
MaxMinutes = Literal[15, 20, 30, 45]

DIET_CHOICES = get_args(Diet)
CUISINE_CHOICES = get_args(Cuisine)
PRIORITY_CHOICES = get_args(Priority)
MAX_MINUTES_CHOICES = get_args(MaxMinutes)

# What a new profile starts with. These match the use-cases.md defaults for a fresh session.
DEFAULT_PREFERENCES = {
    "diet": "Vegetarian",
    "cuisine": "Any",
    "max_minutes": 20,
    "priority": "Best pantry match",
    "high_protein": True,
}

DEFAULT_UNIT = "count"
MAX_QUANTITY = 1_000_000
MAX_RESTRICTIONS = 100

_USERNAME_RE = re.compile(r"^\w[\w .-]{0,63}$")


def normalize_username(value: str) -> str:
    """Lowercase and tidy a profile name. Raises ValueError if it cannot be used."""
    cleaned = " ".join(str(value).split()).lower()
    if not _USERNAME_RE.fullmatch(cleaned):
        raise ValueError(
            "Profile names must be 1-64 characters and use only letters, numbers, spaces, '.', '_', or '-'."
        )
    return cleaned


def _collapse_whitespace(value):
    return " ".join(value.split()) if isinstance(value, str) else value


def _clean_unit(value):
    cleaned = _collapse_whitespace(value)
    return DEFAULT_UNIT if cleaned == "" else cleaned


Username = Annotated[str, AfterValidator(normalize_username)]
IngredientName = Annotated[str, BeforeValidator(_collapse_whitespace), StringConstraints(min_length=1, max_length=120)]
Unit = Annotated[str, BeforeValidator(_clean_unit), StringConstraints(min_length=1, max_length=40)]
Quantity = Annotated[float, Field(strict=True, ge=0, le=MAX_QUANTITY, allow_inf_nan=False)]
RestrictionTerm = Annotated[str, BeforeValidator(_collapse_whitespace), StringConstraints(min_length=1, max_length=80)]


class User(BaseModel):
    id: int
    username: str
    created_at: str


class PantryItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: IngredientName
    quantity: Quantity
    unit: Unit = DEFAULT_UNIT


class PantryItemUpdate(BaseModel):
    """Only the fields sent are changed."""

    model_config = ConfigDict(extra="forbid")

    name: IngredientName | None = None
    quantity: Quantity | None = None
    unit: Unit | None = None

    @model_validator(mode="after")
    def _requires_real_values(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one of name, quantity, or unit.")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("name, quantity, and unit cannot be null.")
        return self


class PantryItem(BaseModel):
    id: int
    name: str
    quantity: float
    unit: str
    created_at: str
    updated_at: str


class Preferences(BaseModel):
    diet: Diet
    cuisine: Cuisine
    max_minutes: MaxMinutes | None
    priority: Priority
    high_protein: bool
    dietary_restrictions: list[str]
    updated_at: str


class PreferencesUpdate(BaseModel):
    """Only the fields sent are changed.

    max_minutes may be null, which means no time limit. dietary_restrictions
    replaces the whole saved list, so an empty list clears it.
    """

    model_config = ConfigDict(extra="forbid")

    diet: Diet | None = None
    cuisine: Cuisine | None = None
    max_minutes: MaxMinutes | None = None
    priority: Priority | None = None
    high_protein: bool | None = None
    dietary_restrictions: Annotated[list[RestrictionTerm], Field(max_length=MAX_RESTRICTIONS)] | None = None

    @model_validator(mode="after")
    def _requires_real_values(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one preference to change.")
        nullable = {"max_minutes"}
        if any(getattr(self, field) is None for field in self.model_fields_set - nullable):
            raise ValueError("Only max_minutes can be null.")
        return self
