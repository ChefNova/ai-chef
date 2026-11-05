# ChefNova — Architecture & Dataflow

## System overview

ChefNova is a Streamlit web application that lets users upload grocery receipts and receive personalized recipe recommendations powered by LLMs.

```
┌─────────────────────────────────────────────────────────┐
│                  User (Browser)                          │
│          Streamlit UI  ·  ChefNova_app_UI.py            │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP (localhost:8501)
         ┌──────────▼──────────┐
         │   Streamlit Server  │
         │   (Python process)  │
         └──┬──────────────────┘
            │
    ┌───────▼──────────────────────────────────────┐
    │              Application Layer               │
    │                                              │
    │  receipt_extractor.py   ──► Tesseract OCR   │
    │  receipt_validator.py   ──► Pydantic         │
    │  recipe_recommendations.py ──► LLM clients  │
    │  schemas.py             ──► Pydantic models  │
    └───────┬──────────────────────────────────────┘
            │
    ┌───────▼──────────────────────────────────────┐
    │              External APIs                   │
    │                                              │
    │  Groq API  (primary)   qwen/qwen3.8-27b     │
    │  Gemini API (fallback) gemini-3.8-flash      │
    └──────────────────────────────────────────────┘
```

## Component descriptions

### `ChefNova_app_UI.py`
Streamlit entry point. Manages session state (pantry items, user profile, dietary preferences), renders the receipt upload widget, and calls downstream modules.

### `receipt_extractor.py`
Runs Tesseract OCR on uploaded receipt images to extract raw text, then sends it to the receipt extraction LLM prompt (`app/prompts/receipt_extraction.md`) for structured JSON output.

### `receipt_validator.py`
Validates extracted JSON against the `ReceiptExtraction` Pydantic schema. Rejects or flags items with low confidence scores.

### `schemas.py`
Single source of truth for Pydantic data models: `GroceryItem`, `ReceiptExtraction`. Shared across extractor, validator, and recommendations modules.

### `recipe_recommendations.py`
Builds the recipe prompt from pantry state and user constraints, calls Groq (primary) with Gemini as fallback, and parses / ranks the JSON response.

### `app/prompts/`
Version-controlled prompt files and model parameter documentation. Each prompt file contains the system message, model settings, output schema, and few-shot examples.

## Dataflow

```
Receipt Image (PNG/JPG)
        │
        ▼
  Tesseract OCR ──► raw text
        │
        ▼
  receipt_extractor.py ──► LLM (Gemini) ──► JSON
        │
        ▼
  receipt_validator.py ──► Pydantic validation
        │
        ▼
  Session pantry state (Streamlit)
        │
        ▼
  recipe_recommendations.py ──► LLM (Groq / Gemini fallback) ──► JSON recipes
        │
        ▼
  Ranked & filtered recipe cards (UI)
```

## Technology stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit |
| OCR | Tesseract 5.x + pytesseract |
| Data validation | Pydantic v2 |
| Primary LLM | Groq — qwen/qwen3.8-27b |
| Fallback LLM | Google Gemini — gemini-3.8-flash |
| Language | Python 3.11+ |
| Testing | pytest |

## Deployment

The app runs locally. No database or persistent storage is used — all state lives in Streamlit's session state for the duration of a session.
