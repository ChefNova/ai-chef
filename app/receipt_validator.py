import re
from typing import Any


# Conservative bounds used to flag suspicious receipt values for user review.
# These rules do not auto-correct the model output.
MAX_REASONABLE_WEIGHT_LB = 50.0
MAX_REASONABLE_WEIGHT_KG = 25.0
MAX_REASONABLE_COUNT = 100.0


def validate_item(item: Any) -> list[str]:
    """Return review warnings for one extracted grocery item."""
    warnings: list[str] = []

    quantity = getattr(item, "quantity", None)
    unit = (getattr(item, "unit", None) or "").strip().lower()
    confidence = getattr(item, "confidence", None)

    if quantity is not None and quantity < 0:
        warnings.append("Quantity cannot be negative.")

    if quantity is not None:
        if unit in {"kg", "kilogram", "kilograms"} and quantity > MAX_REASONABLE_WEIGHT_KG:
            warnings.append("Weight is unusually high; verify the receipt value.")
        elif unit in {"lb", "lbs", "pound", "pounds"} and quantity > MAX_REASONABLE_WEIGHT_LB:
            warnings.append("Weight is unusually high; verify the receipt value.")
        elif unit in {"count", "ct", "each", "ea", "piece", "pieces"} and quantity > MAX_REASONABLE_COUNT:
            warnings.append("Item count is unusually high; verify the receipt value.")

    package_size = getattr(item, "package_size", None)
    if package_size:
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(kg|lb|lbs|oz|g|gram|grams)", package_size.lower())
        if match:
            value = float(match.group(1))
            package_unit = match.group(2)
            if package_unit == "kg" and value > MAX_REASONABLE_WEIGHT_KG:
                warnings.append("Package size is unusually high; verify the receipt value.")
            elif package_unit in {"lb", "lbs"} and value > MAX_REASONABLE_WEIGHT_LB:
                warnings.append("Package size is unusually high; verify the receipt value.")

    if confidence is not None and confidence < 0.70:
        warnings.append("Low extraction confidence; verify this item.")

    return warnings


def validate_extraction(extraction: Any) -> dict[int, list[str]]:
    """Return item-indexed warnings without modifying extracted values."""
    warnings: dict[int, list[str]] = {}
    for index, item in enumerate(extraction.items):
        item_warnings = validate_item(item)
        if item_warnings:
            warnings[index] = item_warnings
    return warnings
