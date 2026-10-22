"""Written prompt and strict JSON schema for receipt extraction."""

EXTRACTION_PROMPT = """You extract grocery line items from a receipt or grocery-order image.

Rules:
- Return only JSON that matches the schema. No markdown and no prose.
- A receipt is evidence of a purchase, not of what remains in the kitchen.
- Do not invent items, quantities, or units that are not visible.
- Prices, taxes, totals, and store names are not quantities and are not items.
- If the image is blank, blurry, cut off, or otherwise unreadable, set readable to false, set failure_reason to a short explanation, and set items to an empty array.
- If you can read some lines but not others, return only the readable grocery lines. For a readable line with a missing name, quantity, or unit, set that field to null and list the field in missing_fields. Do not guess a package size.
- Do not fill missing_fields for a field you actually returned.
- Name is the grocery, not the brand code, unless the brand is the only visible description.
"""

EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["readable", "failure_reason", "items"],
    "properties": {
        "readable": {"type": "boolean"},
        "failure_reason": {"type": "string", "nullable": True},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "quantity", "unit", "missing_fields"],
                "properties": {
                    "name": {"type": "string", "nullable": True},
                    "quantity": {"type": "number", "nullable": True},
                    "unit": {"type": "string", "nullable": True},
                    "missing_fields": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["name", "quantity", "unit"]},
                    },
                },
            },
        },
    },
}
