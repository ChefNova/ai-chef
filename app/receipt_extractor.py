import os
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq

from app.schemas import ReceiptExtraction


# ============================================================
# ENVIRONMENT
# ============================================================

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

# These are defaults only.
# API keys should normally be supplied by the application at runtime.
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "qwen/qwen3.8-27b"
)


# ============================================================
# RESULT OBJECT
# ============================================================

@dataclass
class ExtractionResult:
    """
    Result returned by the receipt extraction pipeline.

    source:
        "gemini"         -> Gemini successfully extracted receipt
        "groq_fallback"  -> Gemini failed, Groq succeeded
        "manual_review"  -> Both AI models failed
    """

    source: str
    extraction: Optional[ReceiptExtraction] = None
    ocr_text: Optional[str] = None


# ============================================================
# PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are ChefNova's receipt extraction component.

You will receive OCR text extracted from a grocery receipt.

Convert the OCR text into structured grocery purchase information.

IMPORTANT RULES:

1. Extract grocery and food items only.

2. Ignore:
   - subtotal
   - tax
   - total
   - payment information
   - addresses
   - transaction numbers
   - register information
   - cashier information
   - loyalty information
   - coupons
   - barcodes
   - unrelated household/non-food products

3. Never invent:
   - quantities
   - units
   - package sizes
   - brands
   - ingredients

4. If a field is not supported by the receipt, return null.

5. Normalize obvious receipt abbreviations when reasonably clear.

Examples:
   CHKN BRST BNLS -> Chicken Breast
   GRK YOG -> Greek Yogurt
   ORG -> Organic
   H LDRM -> Haldiram's

6. A receipt is evidence of purchase, NOT proof of current inventory.

7. Keep separate entries when the same item appears with different
   sizes or units.

8. source_text must contain the original OCR text supporting the item.

9. confidence should represent confidence in the extraction.

10. Preserve ambiguity rather than guessing.

11. Pay particular attention to:
    - quantities such as 1, 2, 12
    - weights such as 0.53 lb
    - package sizes such as 32 OZ, 2 LB, 400G
    - prices such as $2.99/lb
    - product descriptions split across multiple OCR lines

Return ONLY the structured JSON requested by the schema.
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
# GEMINI
# ============================================================

def get_gemini_client(api_key: Optional[str] = None):
    """
    Create Gemini client.

    If an API key is supplied by the application at runtime,
    use that key.

    Otherwise, fall back to GEMINI_API_KEY from .env for
    local development.
    """

    api_key = api_key or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Gemini API key was not provided. "
            "Enter a Gemini API key in the application."
        )

    return genai.Client(api_key=api_key)


def extract_with_gemini(
    ocr_text: str,
    api_key: Optional[str] = None,
) -> ReceiptExtraction:
    """
    Primary AI extraction using Gemini.
    """

    client = get_gemini_client(api_key)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Part.from_text(
                    text=(
                        SYSTEM_PROMPT
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
    finally:
        client.close()

    if getattr(response, "parsed", None) is not None:
        return ReceiptExtraction.model_validate(
            response.parsed
        )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return ReceiptExtraction.model_validate_json(
        response.text
    )


# ============================================================
# GROQ
# ============================================================

def get_groq_client(api_key: Optional[str] = None):
    """
    Create Groq client.

    If an API key is supplied by the application at runtime,
    use that key.

    Otherwise, fall back to GROQ_API_KEY from .env for
    local development.
    """

    api_key = api_key or os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Groq API key was not provided. "
            "Enter a Groq API key in the application."
        )

    return Groq(api_key=api_key)


def extract_with_groq(
    ocr_text: str,
    api_key: Optional[str] = None,
) -> ReceiptExtraction:
    """
    Fallback AI extraction using Groq.

    Groq receives the SAME OCR text used by Gemini.
    """

    client = get_groq_client(api_key)
    schema = ReceiptExtraction.model_json_schema()

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    "OCR TEXT FROM RECEIPT:\n\n"
                    + ocr_text
                ),
            },
        ],
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "receipt_extraction",
                "schema": schema,
            },
        },
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    parsed = json.loads(content)
    return ReceiptExtraction.model_validate(parsed)


# ============================================================
# MAIN EXTRACTION PIPELINE
# ============================================================

def extract_receipt(
    image_path: str,
    gemini_api_key: Optional[str] = None,
    groq_api_key: Optional[str] = None,
) -> ExtractionResult:
    """
    Run the complete receipt extraction pipeline.

    Pipeline:
        Tesseract OCR
            ↓
        Gemini
            ↓
        Groq fallback
            ↓
        Manual review

    API keys are supplied by the application at runtime.

    For local development, the functions can fall back to
    GEMINI_API_KEY and GROQ_API_KEY from .env.
    """

    print("\n[1/3] Running local OCR...")

    ocr_text = extract_text_with_ocr(image_path)

    print("[OK] OCR completed.")

    print("\n========== OCR TEXT ==========")
    print(ocr_text)
    print("==============================\n")

    # --------------------------------------------------------
    # Gemini
    # --------------------------------------------------------

    print(
        f"[2/3] Trying Gemini ({GEMINI_MODEL})..."
    )

    for attempt in range(3):
        try:
            result = extract_with_gemini(
                ocr_text,
                api_key=gemini_api_key,
            )

            print("[OK] Gemini extraction succeeded.")

            return ExtractionResult(
                source="gemini",
                extraction=result,
                ocr_text=ocr_text,
            )

        except Exception as error:
            print(
                f"[Gemini attempt {attempt + 1}/3 failed] "
                f"{error}"
            )

            if attempt < 2:
                wait_seconds = 5 * (2 ** attempt)

                print(
                    f"Retrying Gemini in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)

    # --------------------------------------------------------
    # Groq fallback
    # --------------------------------------------------------

    print("\n[3/3] Gemini unavailable.")
    print(f"Trying Groq ({GROQ_MODEL})...")

    try:
        result = extract_with_groq(
            ocr_text,
            api_key=groq_api_key,
        )

        print("[OK] Groq fallback extraction succeeded.")

        return ExtractionResult(
            source="groq_fallback",
            extraction=result,
            ocr_text=ocr_text,
        )

    except Exception as error:
        print(
            f"[Groq fallback failed] {error}"
        )

        print("\nBoth AI extraction services failed.")
        print("Falling back to manual review.")

        return ExtractionResult(
            source="manual_review",
            extraction=None,
            ocr_text=ocr_text,
        )


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "ChefNova receipt extraction pipeline: "
            "Tesseract → Gemini → Groq → manual review"
        )
    )

    parser.add_argument(
        "image",
        help="Path to receipt image (.jpg, .jpeg, .png, .webp)",
    )

    args = parser.parse_args()

    result = extract_receipt(args.image)

    print("\n========== EXTRACTION SOURCE ==========")
    print(result.source)
    print("=======================================\n")

    if result.extraction is not None:

        print("========== STRUCTURED RESULT ==========")

        print(
            result.extraction.model_dump_json(
                indent=2
            )
        )

        print("=======================================")

    else:

        print("========== MANUAL REVIEW ==========")

        print("AI extraction unavailable.")

        print("Review the OCR text below:")

        print(result.ocr_text)

        print("===================================")
