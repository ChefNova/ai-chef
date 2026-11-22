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

## 5b — Accounts and Google sign-in

There are two ways to sign in, and each account gets its own pantry and preferences:

- **Username and password** (works with no setup): *Create account* stores the username, email (lowercased, one account per email), and a salted scrypt hash of the password (never the password). The email is not verified yet. Usernames may not start with `google-`.
- **Google** (optional, needs the steps below): the first Google sign-in creates the account and its starter pantry.

Without `.streamlit/secrets.toml` the Google button is hidden (with no message to visitors) and only username/password sign-in is offered.
Only Google's stable account id (`sub`) is stored, as the profile `google-<sub>`; the email is shown but never saved.

1. In [Google Cloud Console](https://console.cloud.google.com/apis/credentials), create an **OAuth client ID** of type *Web application*.
2. Add the authorized redirect URIs `http://localhost:8501/oauth2callback` (local) and `https://chefnova.streamlit.app/oauth2callback` (deployed).
3. On the OAuth consent screen, leave the app in *Testing* and add each tester's Gmail address, or publish it.
4. Copy the template and fill in the client id, client secret, and a random cookie secret:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

`.streamlit/secrets.toml` is git-ignored. On Streamlit Community Cloud, paste the same `[auth]` block into *App settings → Secrets* with the deployed `redirect_uri`.

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
