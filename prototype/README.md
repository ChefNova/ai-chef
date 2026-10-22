# ChefNova Prototype

Streamlit prototype for ChefNova.

## Run locally
```bash
pip install -r requirements.txt
streamlit run ChefNova_app.py
```

Each receipt scan asks for a Gemini API key before extraction. A saved key, or `GEMINI_API_KEY` when nothing is saved, only prefills that prompt. Checking **Save this key on this computer for later scans** writes it to `prototype/.chefnova/gemini_api_key`, which is gitignored. Optional model override: `GEMINI_MODEL` (default `gemini-3.8-flash`). A busy default model is retried, then `gemini-3.6-flash` is tried. Setting `GEMINI_MODEL` to another model skips that fallback. Reviewed rows are written to inventory only after **Confirm reviewed items**, and only when every row has a valid name, quantity, and unit.

## Tests
From the repository root:
```bash
pip install -r prototype/requirements-dev.txt
pytest
```

## Streamlit Community Cloud
Deploy with `prototype/ChefNova_app.py` as the app entrypoint. Set `GEMINI_API_KEY` in the app secrets.
