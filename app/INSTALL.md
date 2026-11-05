# ChefNova — Local Setup Guide

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| Tesseract OCR | 5.x |
| pip | latest |

---

## 1 — Clone the repository

```bash
git clone https://github.com/ChefNova/ai-chef.git
cd ai-chef
```

## 2 — Create and activate a virtual environment

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

## 3 — Install Python dependencies

```bash
pip install -r app/requirements.txt
```

## 4 — Install Tesseract OCR

| OS | Command |
|----|---------|
| macOS | `brew install tesseract` |
| Ubuntu / Debian | `sudo apt install tesseract-ocr` |
| Windows | Download installer from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH |

Verify: `tesseract --version`

## 5 — Configure environment variables

```bash
cp app/.env.example .env
```

Open `.env` and fill in your API keys (see `.env.example` for field descriptions).

## 6 — Run the app

```bash
streamlit run ChefNova_app_UI.py
```

The app opens at `http://localhost:8501`.

## 7 — Run the test suite

```bash
pytest tests/ -v
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `tesseract: command not found` | Add Tesseract to your system PATH |
| `ModuleNotFoundError` | Re-run `pip install -r app/requirements.txt` |
| API key errors | Ensure `.env` is populated and loaded before running |
| Blank recipe results | Check that `GROQ_API_KEY` or `GEMINI_API_KEY` is valid |
