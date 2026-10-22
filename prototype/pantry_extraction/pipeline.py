"""Turn a model response into review rows. Inventory is not written here."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass, field

from pantry_extraction.validate import ReviewItem, validate_item, validate_row

ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "application/pdf",
}


class MissingApiKey(RuntimeError):
    """Raised when a live model call was requested without GEMINI_API_KEY."""


@dataclass
class ExtractionResult:
    ok: bool
    failure_reason: str | None
    items: list[ReviewItem] = field(default_factory=list)

    @property
    def notice(self) -> str | None:
        if not self.ok:
            return None
        incomplete = [item for item in self.items if not item.ok]
        if not self.items:
            return "No grocery items were found on the receipt."
        if incomplete:
            return (
                f"Read {len(self.items)} line(s). "
                f"{len(incomplete)} still need a name, quantity, or unit before they can be confirmed."
            )
        return f"Read {len(self.items)} grocery line(s). Review them before confirming."


@dataclass
class ConfirmOutcome:
    accepted: bool
    inventory: list
    items: list[ReviewItem]
    message: str


def _failure(reason: str) -> ExtractionResult:
    return ExtractionResult(ok=False, failure_reason=reason, items=[])


def parse_model_output(raw: str) -> ExtractionResult:
    """Apply the schema. Unreadable or invalid JSON yields zero items."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return _failure("The model did not return valid JSON. No items were extracted.")

    if not isinstance(payload, dict):
        return _failure("The model response was not a JSON object. No items were extracted.")

    if "readable" not in payload or not isinstance(payload.get("readable"), bool):
        return _failure("The model response did not say whether the receipt was readable. No items were extracted.")

    if payload["readable"] is False:
        reason = payload.get("failure_reason") or "The receipt could not be read."
        if not isinstance(reason, str) or not reason.strip():
            reason = "The receipt could not be read."
        # Ignore any items the model attached to an unreadable receipt.
        return _failure(reason.strip())

    raw_items = payload.get("items", [])
    if not isinstance(raw_items, list):
        return _failure("The model item list was not an array. No items were extracted.")

    items: list[ReviewItem] = []
    for entry in raw_items:
        if not isinstance(entry, dict):
            items.append(
                ReviewItem(
                    name="",
                    quantity=None,
                    unit="",
                    missing_fields=["name", "quantity", "unit"],
                    errors=["item was not an object"],
                )
            )
            continue
        declared = entry.get("missing_fields") or []
        if not isinstance(declared, list):
            declared = []
        items.append(
            validate_item(
                name=entry.get("name"),
                quantity=entry.get("quantity"),
                unit=entry.get("unit"),
                model_missing=[str(part) for part in declared],
            )
        )
    return ExtractionResult(ok=True, failure_reason=None, items=items)


def extract_receipt(image_bytes: bytes, mime_type: str, model) -> ExtractionResult:
    """Call the model, then parse. Does not write inventory."""
    if not image_bytes:
        return _failure("The receipt file is empty. No items were extracted.")
    if mime_type not in ALLOWED_MIME_TYPES:
        return _failure(f"Unsupported receipt type '{mime_type}'. No items were extracted.")
    try:
        raw = model.extract(image_bytes, mime_type)
    except Exception as exc:  # noqa: BLE001 — surface a failure instead of inventing rows
        return _failure(
            f"Receipt extraction failed ({_public_error(exc)}). No items were extracted."
        )
    return parse_model_output(raw)


def _public_error(exc: Exception) -> str:
    """Class name plus a short message, with API keys stripped out."""
    name = exc.__class__.__name__
    text = " ".join(str(exc).split())
    text = re.sub(r"(?i)([?&]key=)[^&\s\"']+", r"\1[redacted]", text)
    text = re.sub(r"AIza[0-9A-Za-z_\-]{10,}", "[redacted]", text)
    if not text or text == name:
        return name
    if len(text) > 240:
        text = text[:239].rstrip() + "…"
    return f"{name}: {text}"


def confirm_review_into_inventory(inventory: list, rows: list[dict]) -> ConfirmOutcome:
    """Write inventory only when every reviewed row is valid."""
    untouched = deepcopy(inventory)
    if not rows:
        return ConfirmOutcome(False, untouched, [], "Add at least one reviewed item before confirming.")

    items = [validate_row(row) for row in rows]
    if any(not item.ok for item in items):
        return ConfirmOutcome(
            False,
            untouched,
            items,
            "Nothing was added. Fix missing or invalid name, quantity, and unit fields, then confirm again.",
        )

    merged = deepcopy(inventory)
    index = {}
    for existing in merged:
        key = (str(existing.get("Ingredient", "")).strip().lower(), str(existing.get("Unit", "")).strip().lower())
        index[key] = existing

    for item in items:
        name = item.name.title()
        key = (name.lower(), item.unit.lower())
        if key in index:
            index[key]["Quantity"] = index[key].get("Quantity", 0) + item.quantity
        else:
            created = {"Ingredient": name, "Quantity": item.quantity, "Unit": item.unit}
            merged.append(created)
            index[key] = created

    return ConfirmOutcome(True, merged, items, "Reviewed items were added. Confirm the pantry after checking the final list.")
