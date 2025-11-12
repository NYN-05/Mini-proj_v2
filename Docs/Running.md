# EduShield (prototype)

This is a lightweight, runnable prototype of the EduShield end-to-end project described in the documentation.

What is included
- A small synthetic dataset and a training script: `src/train_models.py` (creates a `models/` folder with pickles)
- A Flask web app: `app/app.py` (serves a small UI at `/` and an API at `/detect`)
- Predictor and explainer utilities in `app/utils/`
- Frontend template and JS in `app/templates` and `app/static`
- A pytest test that trains the models and runs a sample prediction: `tests/test_predictor.py`

Quick start (Windows PowerShell)
```powershell
# 1) (optional) create and activate virtualenv
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2) install dependencies
pip install -r requirements.txt

# 3) train models (creates models/)
python src/train_models.py

# 4) run the Flask app
python app/app.py

# 5) open http://localhost:5000 in your browser and paste an email to test

# 6) run tests
pytest -q
```

Notes
- This prototype uses small synthetic data for demonstration. Replace `src/train_models.py` with a real training pipeline (larger dataset, hyperparameter tuning, BERT fine-tuning) for production.

Notes:
- For automated scanning across many users in an institution, consider using a service account with domain-wide delegation (requires Google Workspace admin).
- The script currently extracts `text/plain` parts; for HTML emails it tries to aggregate parts. You may want to improve parsing for complex multipart emails.

