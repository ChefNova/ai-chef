"""Validate a proposed pantry row before it can be confirmed."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

_NAME_RE = re.compile(r"[A-Za-z]")

# Aliases normalize to the unit stored on the pantry row.
_UNIT_ALIASES = {
    "count": "count",
    "ct": "count",
    "item": "item",
    "items": "item",
    "can": "cans",
    "cans": "cans",
    "bag": "bag",
    "bags": "bag",
    "cup": "cups",
    "cups": "cups",
    "container": "container",
    "containers": "container",
    "bulb": "bulb",
    "bulbs": "bulb",
    "lb": "lb",
    "lbs": "lb",
    "pound": "lb",
    "pounds": "lb",
    "oz": "oz",
    "ounce": "oz",
    "ounces": "oz",
    "gallon": "gallon",
    "gallons": "gallon",
    "dozen": "dozen",
    "g": "g",
    "kg": "kg",
    "ml": "ml",
    "l": "l",
    "bunch": "bunch",
    "bunches": "bunch",
    "pack": "pack",
    "packs": "pack",
    "package": "package",
    "packages": "package",
    "bottle": "bottle",
    "bottles": "bottle",
    "jar": "jar",
    "jars": "jar",
    "box": "box",
    "boxes": "box",
    "carton": "carton",
    "cartons": "carton",
}


@dataclass
class ReviewItem:
    name: str
    quantity: float | None
    unit: str
    missing_fields: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing_fields and not self.errors

    def as_review_dict(self) -> dict:
        return {
            "Ingredient": self.name,
            "Quantity": self.quantity,
            "Unit": self.unit,
        }


def _blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return str(value).strip() == ""


def _parse_quantity(value):
    if _blank(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        return text


def validate_item(*, name, quantity, unit, model_missing: list[str] | None = None) -> ReviewItem:
    """Flag missing fields and reject invalid ones. Never invent a value.

    `model_missing` is accepted so callers can pass the schema field through.
    Gaps are computed from the values, so a model cannot hide a blank field
    or mark a valid value as missing.
    """
    del model_missing
    missing: list[str] = []
    errors: list[str] = []

    if _blank(name):
        missing.append("name")
        clean_name = ""
    else:
        clean_name = re.sub(r"\s+", " ", str(name).strip())
        if not _NAME_RE.search(clean_name):
            errors.append("name must contain letters")
        elif len(clean_name) > 80:
            errors.append("name is too long")

    parsed_qty = _parse_quantity(quantity)
    if parsed_qty is None:
        missing.append("quantity")
        clean_qty = None
    elif isinstance(parsed_qty, str) or isinstance(parsed_qty, bool):
        errors.append("quantity must be a number greater than 0")
        clean_qty = None
    elif not math.isfinite(parsed_qty) or parsed_qty <= 0:
        errors.append("quantity must be a number greater than 0")
        clean_qty = None
    else:
        clean_qty = int(parsed_qty) if parsed_qty.is_integer() else parsed_qty

    if _blank(unit):
        missing.append("unit")
        clean_unit = ""
    else:
        token = str(unit).strip().lower()
        if token not in _UNIT_ALIASES:
            errors.append(f"unit '{str(unit).strip()}' is not a recognized grocery unit")
            clean_unit = str(unit).strip()
        else:
            clean_unit = _UNIT_ALIASES[token]

    return ReviewItem(
        name=clean_name,
        quantity=clean_qty,
        unit=clean_unit,
        missing_fields=missing,
        errors=errors,
    )


def validate_row(row: dict) -> ReviewItem:
    missing = row.get("missing_fields") or row.get("Missing fields") or []
    if isinstance(missing, str):
        missing = [part.strip() for part in missing.split(",") if part.strip()]
    return validate_item(
        name=row.get("name", row.get("Ingredient")),
        quantity=row.get("quantity", row.get("Quantity")),
        unit=row.get("unit", row.get("Unit")),
        model_missing=list(missing) if isinstance(missing, (list, tuple)) else [],
    )


def issue_text(item: ReviewItem) -> str:
    parts = [f"missing {name}" for name in item.missing_fields]
    parts.extend(item.errors)
    return "; ".join(parts)
