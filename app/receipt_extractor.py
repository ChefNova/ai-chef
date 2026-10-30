from __future__ import annotations

import os
import json
import re
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    from PIL import Image, ImageEnhance, ImageFilter
except ImportError:
    Image = ImageEnhance = ImageFilter = None

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

try:
    from groq import Groq
except ImportError:
    Groq = None

from app.schemas import ReceiptExtraction


# ============================================================
# ENVIRONMENT
# ============================================================

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "qwen/qwen3.8-27b"
)

# The current Groq on-demand tier reported a 1,000 output-tokens-per-minute
# limit. Cap each extraction response below that limit so the request is not
# rejected before inference. This value applies to both the primary request
# and the existing empty-result retry.
GROQ_MAX_OUTPUT_TOKENS = 850


# ============================================================
# RESULT OBJECT
# ============================================================

@dataclass
class ExtractionResult:
    """
    Result returned by the receipt extraction pipeline.

    source:
        "groq"            -> Groq successfully extracted receipt
        "gemini_fallback" -> Groq failed, Gemini succeeded
        "manual_review"   -> Both AI models failed
    """

    source: str
    extraction: Optional[ReceiptExtraction] = None
    ocr_text: Optional[str] = None
    errors: list[str] = field(default_factory=list)


# ============================================================
# PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are ChefNova's grocery-receipt line-item extractor. Your job is to extract
products from OCR, not to summarize the receipt or decide whether the pantry is
currently stocked.

MANDATORY EXTRACTION BEHAVIOR:
- Read the OCR from top to bottom, line by line.
- Extract EVERY identifiable grocery/food product purchased. Do not stop after
  the first item, and do not return an empty items array when product lines are
  present.
- Return items=[] ONLY when the OCR genuinely contains no identifiable grocery
  or food products. A noisy, abbreviated, or partly unreadable name is not a
  reason to skip a likely product; preserve the best-supported name and lower
  confidence when necessary.
- Treat each product/price line as a candidate item. Receipt descriptions and
  their quantity/weight/price lines may be split across adjacent OCR lines;
  combine the lines that clearly belong together into one item.
- When an item is identifiable but a detail is unclear, include the item and use
  null for that detail. Do not omit the whole item because quantity, brand, unit,
  or package size is unknown.
- If uncertain whether a candidate is a food product, include it with lower
  confidence unless the OCR clearly identifies it as non-food. Do not silently
  discard plausible food products.

WHAT TO EXTRACT:
- Food, produce, meat, dairy, eggs, beverages, packaged groceries, snacks,
  spices, sauces, and other edible grocery products.
- One object per purchased product. Keep distinct products and distinct package
  sizes separate.

WHAT TO IGNORE:
- Subtotal, tax, total, payment/card information, addresses, transaction or
  register numbers, cashier information, loyalty information, coupons, and
  barcodes.
- Clearly non-food household products (for example paper towels or detergent).

FIELDS AND ACCURACY:
- name: human-readable product name. Normalize abbreviations only when the
  evidence supports it (e.g., CHKN BRST BNLS -> Chicken Breast; GRK YOG -> Greek
  Yogurt; ORG -> Organic).
- quantity: numeric amount purchased when supported by the OCR. For weighted
  produce, use the printed weight and the matching unit (e.g., 1.12 and "lb").
  If quantity is not clear, use null; do not invent it.
- unit: the unit for quantity (e.g., lb, oz, count), or null.
- package_size: explicitly printed package size (e.g., 32 OZ, 2 LB, 400G), or
  null. Do not confuse a line price or extended price with package size.
- brand: only when supported by the receipt, otherwise null.
- confidence: a number from 0 to 1 representing extraction certainty. Use lower
  confidence for OCR ambiguity rather than omitting a plausible product.
- source_text: the original OCR line or adjacent lines supporting that item.
- Do not infer that purchased groceries are still in the user's pantry.

EXAMPLES OF LINE JOINING:
OCR: "BANANAS ..." followed by "1.12 lb @ $0.69/lb"
=> extract Bananas, quantity 1.12, unit "lb", and include both lines in source_text.
OCR: "ORG, BABY SPINACH 5oz 3.49" followed by "1 @ 3.49"
=> extract Organic Baby Spinach, quantity 1, package_size "5 oz" when legible.
OCR: "TAX ..." or "TOTAL ..." => do not extract as a product.

Return ONLY the structured JSON required by the schema. The items array MUST
contain every identifiable food product from the OCR. Never use an empty array
as a shortcut or as a substitute for handling OCR uncertainty.
"""


# ============================================================
# OCR
# ============================================================

def preprocess_receipt(image: Image.Image) -> Image.Image:
    """
    Basic preprocessing for receipt OCR.
    """

    image = image.convert("L")

    image = ImageEnhance.Contrast(image).enhance(2.0)

    image = image.filter(ImageFilter.SHARPEN)

    return image


def extract_text_with_ocr(image_path: str) -> str:
    """
    Extract raw receipt text using local Tesseract OCR.
    """

    if Image is None or ImageEnhance is None or ImageFilter is None or pytesseract is None:
        raise RuntimeError(
            "Receipt OCR dependencies are missing. Install requirements.txt and Tesseract."
        )

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Receipt image not found: {path}"
        )

    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    if path.suffix.lower() not in supported_extensions:
        raise ValueError(
            "Supported images: .jpg, .jpeg, .png, .webp"
        )

    image = Image.open(path)

    processed_image = preprocess_receipt(image)

    ocr_text = pytesseract.image_to_string(
        processed_image,
        config="--psm 6",
    )

    if not ocr_text.strip():
        raise RuntimeError(
            "OCR returned no text from the receipt."
        )

    return ocr_text


# ============================================================
# GROQ RESPONSE-FORMAT HANDLING
# ============================================================

def _is_groq_schema_error(exc: Exception) -> bool:
    """Identify schema/response-format errors eligible for a JSON-mode retry."""
    message = str(exc).lower()
    status_code = getattr(exc, "status_code", None)
    return (
        status_code == 400 and any(
            token in message
            for token in ("schema", "response_format", "response format", "additionalproperties")
        )
    ) or any(
        token in message
        for token in (
            "invalid json schema",
            "schema_kind",
            "additionalproperties",
            "additional properties",
            "invalid schema for response_format",
        )
    )


def groq_chat_completion_with_schema_fallback(
    client,
    *,
    model: str,
    messages: list[dict[str, str]],
    schema: dict,
    **kwargs,
):
    """Reproduce the previously working Groq request: best-effort JSON schema.

    The old Gemini-primary implementation omitted `strict: true` and sent the
    Pydantic schema as generated. Keep that behavior for the first Groq attempt.
    If Groq rejects the schema, retry the same prompt in JSON-object mode; the
    caller then validates the result with Pydantic.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "receipt_extraction",
                    "schema": schema,
                },
            },
            **kwargs,
        )
        return response, "best_effort_schema"
    except Exception as exc:
        if not _is_groq_schema_error(exc):
            raise
        print(
            "[Groq] Best-effort JSON schema was rejected; retrying once with JSON-object mode: "
            f"{exc}"
        )
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            **kwargs,
        )
        return response, "json_object_schema_fallback"


def _repair_weighted_quantities(extraction: ReceiptExtraction) -> ReceiptExtraction:
    """
    Correct a common receipt-extraction error without changing item detection.

    For items sold by weight, the receipt often contains a real weight such as
    ``1.12 lb`` followed by an extended price. The model can incorrectly return
    quantity=1 and unit=lb because it interprets the trailing purchase/count
    marker as the quantity. If the supporting source_text contains an explicit
    weight, use that printed weight. Package-size quantities such as ``12 CT``
    or ``64 OZ`` are left untouched because those belong in package_size.
    """
    weight_pattern = re.compile(
        r"(?<![\d.])(\d+(?:\.\d+)?)\s*(lb|lbs|pounds?|kg|kgs|kilograms?)\b",
        re.IGNORECASE,
    )

    for item in extraction.items:
        unit = (item.unit or "").strip().lower()
        if unit not in {"lb", "lbs", "pound", "pounds", "kg", "kgs", "kilogram", "kilograms"}:
            continue

        matches = list(weight_pattern.finditer(item.source_text or ""))
        if not matches:
            continue

        # Prefer the explicit weight before a per-weight price marker.
        match = matches[0]
        value = float(match.group(1))
        normalized_unit = "lb" if match.group(2).lower().startswith(("lb", "pound")) else "kg"

        # Only repair when the printed source disagrees with the extracted
        # quantity. This preserves a correct model result unchanged.
        if item.quantity is None or abs(float(item.quantity) - value) > 1e-9:
            item.quantity = value
        item.unit = normalized_unit

    return extraction


def _require_items(extraction, provider):
    """Reject an apparently valid but empty AI extraction."""
    if extraction is None or not extraction.items:
        raise RuntimeError(
            f"{provider} returned a valid response but extracted zero grocery items."
        )
    return extraction


# ============================================================
# GEMINI
# ============================================================

def extract_with_gemini(ocr_text: str, api_key: str) -> ReceiptExtraction:
    """Fallback AI extraction using Gemini, with a lighter-model deadline retry."""
    if not api_key:
        raise RuntimeError("Gemini API key is missing.")
    if genai is None or types is None:
        raise RuntimeError("Gemini SDK is missing. Install the google-genai package.")

    # Allow enough client-side time for structured output, then use a lighter
    # stable Flash model if the configured model returns a server deadline error.
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60000),
    )
    fallback_model = os.getenv("GEMINI_DEADLINE_FALLBACK_MODEL", "gemini-3.6-flash")
    models_to_try = [GEMINI_MODEL, fallback_model] if fallback_model != GEMINI_MODEL else [GEMINI_MODEL]
    last_error = None
    response = None
    try:
        for attempt, model in enumerate(models_to_try):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_text(
                            text=(
                                SYSTEM_PROMPT
                                + "\n\nExtract every identifiable grocery product line. "
                                + "Do not return an empty items array when product lines are present."
                                + "\n\nOCR TEXT FROM RECEIPT:\n"
                                + ocr_text
                            )
                        )
                    ],
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                        response_schema=ReceiptExtraction,
                    ),
                )
                break
            except Exception as exc:
                last_error = exc
                message = str(exc).upper()
                transient_deadline = (
                    "504" in message
                    or "DEADLINE_EXCEEDED" in message
                    or "DEADLINE EXPIRED" in message
                )
                if attempt == 0 and transient_deadline and len(models_to_try) > 1:
                    print(
                        f"[Gemini] {model} hit a deadline; retrying with {models_to_try[1]}."
                    )
                    time.sleep(1.0)
                    continue
                raise RuntimeError(f"Gemini model {model} failed: {exc}") from exc
        if response is None:
            raise RuntimeError(f"Gemini returned no response. Last error: {last_error}")
    finally:
        try:
            client.close()
        except Exception:
            pass

    if getattr(response, "parsed", None) is not None:
        extraction = ReceiptExtraction.model_validate(response.parsed)
    elif getattr(response, "text", None):
        extraction = ReceiptExtraction.model_validate_json(response.text)
    else:
        raise RuntimeError("Gemini returned an empty response.")
    return _repair_weighted_quantities(_require_items(extraction, f"Gemini ({model})"))


# ============================================================
# GROQ
# ============================================================

def _parse_groq_response(response, attempt_name: str) -> tuple[ReceiptExtraction, str]:
    """Parse and validate a Groq JSON response; return raw content for diagnostics."""
    content = getattr(response.choices[0].message, "content", None)
    if not content:
        raise RuntimeError(f"Groq {attempt_name} returned an empty response body.")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Groq {attempt_name} returned invalid JSON: {exc}; body={content[:700]!r}") from exc
    try:
        extraction = ReceiptExtraction.model_validate(parsed)
    except Exception as exc:
        raise RuntimeError(f"Groq {attempt_name} returned JSON that failed validation: {exc}; body={content[:700]!r}") from exc
    return extraction, content


def groq_extract_items_with_empty_retry(
    client,
    *,
    model: str,
    messages: list[dict[str, str]],
    retry_messages: list[dict[str, str]],
    schema: dict[str, Any],
    task_label: str = "grocery extraction",
    **kwargs,
) -> tuple[ReceiptExtraction, str]:
    """Run Groq using the prior best-effort schema path; retry empty results in JSON mode.

    Schema validation guarantees output shape, not that the model found products. This
    helper handles that semantic-empty case explicitly for receipt, typed, and voice flows.
    """
    response, mode = groq_chat_completion_with_schema_fallback(
        client,
        model=model,
        messages=messages,
        schema=schema,
        **kwargs,
    )
    extraction, first_raw = _parse_groq_response(response, "primary")
    if extraction.items:
        return _repair_weighted_quantities(extraction), mode

    print(
        f"[Groq] {task_label}: primary response was valid but empty; "
        "retrying with a focused prompt in JSON-object mode."
    )
    retry_response = client.chat.completions.create(
        model=model,
        messages=retry_messages,
        response_format={"type": "json_object"},
        **kwargs,
    )
    retry_extraction, retry_raw = _parse_groq_response(retry_response, "empty-result retry")
    if retry_extraction.items:
        return retry_extraction, f"{mode}+json_object_empty_retry"

    raise RuntimeError(
        f"Groq returned zero grocery items after the primary request and focused retry for {task_label}. "
        f"Primary response ({mode}): {first_raw[:500]!r}; "
        f"retry response: {retry_raw[:500]!r}"
    )


def extract_with_groq(ocr_text: str, api_key: str) -> ReceiptExtraction:
    """Primary Groq extraction matching the previously working fallback request; recover empty results."""
    if not api_key:
        raise RuntimeError("Groq API key is missing.")
    if Groq is None:
        raise RuntimeError("Groq SDK is missing. Install the groq package.")

    client = Groq(api_key=api_key)
    # Intentionally match the previously working Gemini-primary -> Groq fallback:
    # same system prompt, same user text wrapper, same Pydantic schema, and NO strict=True.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Extract every identifiable grocery/food line item from the OCR below. "
                "The OCR contains a real receipt: do not summarize it. Include all plausible "
                "food products, join split description/weight lines, use null for unknown fields, "
                "and return an empty items array only if there are truly no identifiable food products. "
                "Each item must contain name, quantity, unit, package_size, brand, confidence, and source_text. "
                "Use numeric quantity or null; confidence must be between 0 and 1; source_text must quote "
                "the supporting OCR line(s).\n\n"
                "OCR TEXT FROM RECEIPT:\n\n" + ocr_text
            ),
        },
    ]
    retry_messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\nThis is a required extraction task. Empty output is incorrect whenever a plausible food product line exists.",
        },
        {
            "role": "user",
            "content": (
                "Your previous response incorrectly returned zero items. Perform a fresh, literal pass "
                "over every OCR line. First identify all candidate product lines, then return one item "
                "for each identifiable food product. Join a product line with immediately adjacent "
                "weight/quantity lines where they clearly belong together. If any field is unknown, "
                "set that field to null; do not drop the product. Do not include tax, totals, payment, "
                "or clearly non-food items. Return JSON only, following this exact shape and field names: "
                '{"items":[{"name":"Organic Bananas","quantity":1.12,"unit":"lb",'
                '"package_size":null,"brand":null,"confidence":0.95,'
                '"source_text":"BANANAS ...\\n1.12 lb @ $0.69/lb"}]}. '
                "Every returned item must include all seven keys: name, quantity, unit, package_size, "
                "brand, confidence, source_text. Use null for unknown quantity/unit/package_size/brand; "
                "never omit required keys.\n\n"
                "OCR TEXT FROM RECEIPT:\n\n" + ocr_text
            ),
        },
    ]
    try:
        extraction, mode = groq_extract_items_with_empty_retry(
            client,
            model=GROQ_MODEL,
            messages=messages,
            retry_messages=retry_messages,
            schema=ReceiptExtraction.model_json_schema(),
            task_label="receipt extraction",
            temperature=0,
            max_completion_tokens=GROQ_MAX_OUTPUT_TOKENS,
        )
        print(f"[Groq] Response format used: {mode}")
        return extraction
    finally:
        try:
            client.close()
        except Exception:
            pass


# ============================================================
# MAIN EXTRACTION PIPELINE
# ============================================================

def extract_receipt(
    image_path: str,
    gemini_api_key: Optional[str] = None,
    groq_api_key: Optional[str] = None,
) -> ExtractionResult:
    """Run OCR, Groq primary extraction, then Gemini fallback."""

    gemini_api_key = (gemini_api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    groq_api_key = (groq_api_key or os.getenv("GROQ_API_KEY", "")).strip()

    print("\n[1/3] Running local OCR...")
    ocr_text = extract_text_with_ocr(image_path)
    print("[OK] OCR completed.")
    print("\n========== OCR TEXT ==========")
    print(ocr_text)
    print("==============================\n")

    errors: list[str] = []

    # PRIMARY: Groq.
    if groq_api_key:
        print(f"[2/3] Trying Groq ({GROQ_MODEL})...")
        try:
            result = extract_with_groq(ocr_text, groq_api_key)
            print(f"[OK] Groq extracted {len(result.items)} grocery item(s).")
            return ExtractionResult(source="groq", extraction=result, ocr_text=ocr_text)
        except Exception as groq_error:
            detail = f"Groq: {type(groq_error).__name__}: {groq_error}"
            errors.append(detail)
            print(f"[Groq primary failed] {detail}")
    else:
        detail = "Groq: skipped because no Groq API key was provided."
        errors.append(detail)
        print(f"[2/3] {detail}")

    # FALLBACK: Gemini.
    if gemini_api_key:
        print(f"\n[3/3] Trying Gemini fallback ({GEMINI_MODEL})...")
        try:
            result = extract_with_gemini(ocr_text, gemini_api_key)
            print(f"[OK] Gemini extracted {len(result.items)} grocery item(s).")
            return ExtractionResult(
                source="gemini_fallback", extraction=result, ocr_text=ocr_text,
                errors=errors,
            )
        except Exception as gemini_error:
            detail = f"Gemini fallback: {type(gemini_error).__name__}: {gemini_error}"
            errors.append(detail)
            print(f"[Gemini fallback failed] {detail}")
    else:
        detail = "Gemini fallback: skipped because no Gemini API key was provided."
        errors.append(detail)
        print(f"[3/3] {detail}")

    print("\nBoth AI extraction services failed. Falling back to manual review.")
    return ExtractionResult(
        source="manual_review",
        extraction=None,
        ocr_text=ocr_text,
        errors=errors,
    )


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "ChefNova receipt extraction pipeline: "
            "Tesseract → Groq → Gemini → manual review"
        )
    )

    parser.add_argument(
        "image",
        help=(
            "Path to receipt image "
            "(.jpg, .jpeg, .png, .webp)"
        ),
    )

    args = parser.parse_args()

    result = extract_receipt(
        args.image
    )

    print(
        "\n========== EXTRACTION SOURCE =========="
    )

    print(result.source)

    print(
        "=======================================\n"
    )

    if result.extraction is not None:

        print(
            "========== STRUCTURED RESULT =========="
        )

        print(
            result.extraction.model_dump_json(
                indent=2
            )
        )

        print(
            "======================================="
        )

    else:

        print(
            "========== MANUAL REVIEW =========="
        )

        print(
            "AI extraction unavailable."
        )

        print(
            "Review the OCR text below:"
        )

        print(
            result.ocr_text
        )

        print(
            "==================================="
        )