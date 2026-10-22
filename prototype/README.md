# ChefNova Prototype

Streamlit prototype for ChefNova.

## Run locally
```bash
pip install -r requirements.txt
streamlit run ChefNova_app.py
```

Receipt reading calls Gemini only when `GEMINI_API_KEY` is set. Optional override: `GEMINI_MODEL` (default `gemini-2.5-flash`). Without the key, extraction stops with an error and does not invent items. Reviewed rows are written to inventory only after **Confirm reviewed items**, and only when every row has a valid name, quantity, and unit.

## Tests
From the repository root:
```bash
pip install -r prototype/requirements-dev.txt
pytest
```

## Streamlit Community Cloud
Deploy with `prototype/ChefNova_app.py` as the app entrypoint. Set `GEMINI_API_KEY` in the app secrets.
