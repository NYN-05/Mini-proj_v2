# EduShield — Detailed Project Report

Below is a concise but thorough report covering the project's purpose/ideas, tech stack, architecture and data flow, file-by-file responsibilities, ML pipeline details, analytics, testing/docs, quality gate checks performed, and recommended next steps & improvements.

## Snapshot / One-line summary

EduShield is a lightweight Flask-based prototype for academic-phishing detection that combines classical ML (TF-IDF + stacked classifiers) with URL analysis, simple explainability and an analytics module backed by SQLite. It includes a training script, an API/UI, and an educational tips module.

## Key ideas & features implemented in the codebase

- Ensemble ML approach: TF-IDF vectorizer + stacked models (LogisticRegression, MultinomialNB, LinearSVC wrapped with calibration) with a stacking classifier.
- Combined heuristics: model confidence + URL risk analysis + header/urgency signals to compute a final score.
- URL filtering: detection of shorteners, suspicious TLDs, homograph (punycode) detection, IP-address URLs, path inspection, anchor mismatch detection.
- Explainability: highlight keywords and produce human-readable risk factors.
- Analytics: local SQLite DB storing prediction history, daily statistics, phishing patterns, model performance, and functions for extracting analytics.
- Education module: endpoints that return categorized security tips for users.
 - Lightweight training pipeline: `src/train_from_csv.py` generates TF-IDF and model artifacts and trains from the canonical `Phishing_Email.csv` located at the project root.
- Feature flags in config to enable/disable analytics/admin/education/advanced detection.
- Prototype-ready quick start flow and pytest integration (test that runs training + sample prediction).

## Tech stack (in repo)

- Language: Python 3.x
- Web framework: Flask (see `requirements.txt` Flask==2.2.5)
- ML: scikit-learn (stacking, TF-IDF, LogisticRegression, MultinomialNB, LinearSVC)
- Data libs: pandas, numpy
- Model persistence: joblib
- DB: SQLite for analytics (via Python sqlite3)
- Testing: pytest
- Other: nltk is listed though not heavily referenced in files we inspected

Files consulted to derive this: `requirements.txt`, `app.py`, `config.py`, `src/train_from_csv.py`, `app/core/*`, `app/modules/*`, `README.md`.

## Architecture & runtime overview

### High-level runtime components

- Flask application factory: `app.py` (creates app instance, registers blueprints)
- Core detection blueprint: `routes.py` providing:
	- `GET /` (UI)
	- `POST /detect` (main API): accepts `email_text` and optional metadata, runs ML + URL filter, logs analytics (if enabled) and returns classification, confidence, explanation and URL analysis structure.
- ML loading & prediction: `predictor.py` loads model artifacts and provides `ModelBundle` and `predict_phishing()`.
- URL analysis: `url_filter.py` performs extraction + per-URL scoring and provides `url_features_from_text()` used at training time and runtime.
- Explainability: `explainer.py` highlights keywords and produces risk factors from predictions.
- Analytics module: `database.py` sets up SQLite schema and provides logging and analytics queries.
- Admin/education blueprints: `routes.py`, `routes.py` + `tips.py`
- Training script: `src/train_from_csv.py` to build models and save artifacts to `models` (TF-IDF, logistic, nb, svm, stacking/pipeline).

### Data & artifact flow

1. Training: `src/train_from_csv.py` builds TF-IDF vectorizer, extracts URL-derived numerical features (via `app.core.url_filter.url_features_from_text`), stacks classifiers, saves artifacts to `models` (`tfidf.pkl`, `logistic.pkl`, `nb.pkl`, `svm.pkl`, `stacking.pkl`, `pipeline.pkl`).
2. Runtime: `app/core/routes.detect_phishing` loads models via `ModelBundle` and uses `predict_phishing()` to compute ML confidence. `filter_urls()` is run to get URL analysis. The endpoint combines scores to produce a final classification and response.
3. Analytics Logging (if enabled): `log_prediction()` writes the prediction and metadata to SQLite; additional functions update daily stats and patterns.

### Feature flags (in `config.py`)

`analytics_enabled`, `admin_dashboard_enabled`, `education_module_enabled`, `advanced_detection_enabled` (advanced detection currently disabled by default in config).

## File-by-file mapping (key files, responsibilities)

- `requirements.txt`
	- Declares dependencies: Flask, scikit-learn, pandas, numpy, joblib, nltk, pytest.
- `app.py`
	- Application factory and blueprint registration. Initializes analytics DB when enabled.
- `config.py`
	- Central configuration (paths, model files, TF-IDF params, thresholds, TLDs, URL shorteners, weights, feature flags).
- `__init__.py`
	- Package init for `app`.
- `predictor.py`
	- `ModelBundle`: loads pipeline or artifact files.
	- `predict_phishing()`: main ML + heuristic combination compute; builds ensemble score; calculates urgency, header risk and final score; returns dict with classification, confidence, model_probs, urgency & other diagnostics.
	- Utility functions: `calculate_urgency_score`, `calculate_phishing_indicators_score`, `extract_academic_keywords`.
- `url_filter.py`
	- URL extraction, homograph detection, path/suspicious pattern checks, per-URL `analyze_single_url()`, `filter_urls()` and `url_features_from_text()` (returns numeric features used at training/prediction). Shortener resolution via network calls has been removed.
- `explainer.py`
	- `highlight_keywords()` (wraps tokens in spans) and `risk_factors_from_prediction()`.
- `routes.py` (core)
	- Flask blueprint exposing `/` and `/detect`, orchestrates ML + URL analysis + analytics logging + response shaping.
- `advanced_detection.py`
	- Compatibility wrapper that exposes `comprehensive_phishing_detection()` combining ML and URL heuristics (used by tests and higher-level demos). This also proxies `filter_urls`.
- `database.py` (analytics)
	- SQLite schema & helpers: `init_db()`, `log_prediction()`, `update_daily_statistics()`, `get_analytics_data()`, `update_phishing_patterns()`.
- `routes.py` (admin)
	- Admin dashboard route (render `admin_dashboard.html`).
- `tips.py` and `routes.py` (education)
	- Provide security tips endpoint.
- `src/train_from_csv.py`
	- Training pipeline (synthetic dataset + augmentation), vectorizer fitting, stacking model training, evaluation, and artifact saving (`pipeline.pkl`, `stacking.pkl`, `tfidf.pkl`, etc.).
- `models/` (artifacts created by training): expected `tfidf.pkl`, `logistic.pkl`, `nb.pkl`, `svm.pkl`, `stacking.pkl`, `pipeline.pkl`
- `templates/` and `static/` (frontend UI & assets): simple UI referenced by `routes.py`.
- `test_predictor.py`
	- Pytest that runs the training script and executes a sample prediction to validate pipeline and API functions.

## ML pipeline specifics & design notes

- **Input features:**
	- TF-IDF (configured in `config.py`, `max_features` 5000, `ngram` (1,3)).
	- URL-derived numerical features appended to TF-IDF (see `url_features_from_text()`).
	- Header-based features (SPF/DKIM/DMARC presence derived at prediction time).
	- Urgency & indicator scores (keyword/regex heuristics).
- **Models:**
	- LogisticRegression
	- MultinomialNB
	- LinearSVC wrapped with `CalibratedClassifierCV` to expose probabilities
	- `StackingClassifier` trained with these base estimators and a logistic final estimator
- **Training script augmentations:**
	- Homoglyph obfuscations, HTML wrapping, punctuation insertion to produce robustness to simple obfuscation attacks.
- **Persistence:**
	- Models saved with joblib; pipeline saved as helper dict object with vectorizer and stacking.
- **Prediction logic:**
	- Use pipeline `predict_proba` if available
	- Fallback to averaging probs/converted decision function outputs where necessary
	- Combine ensemble score with URL risk and header signals using configurable weights to arrive at final classification threshold (>= 0.5 typically PHISHING; URL suspiciousness can force PHISHING)
- **Explainability:**
	- Keywords extraction and simple highlight + risk factor list, model probabilities returned as part of response.

## Analytics & database

- Database file (SQLite) located by config: `edushield_analytics.db`.
- Tables:
	- `prediction_history`, `daily_statistics`, `phishing_patterns`, `user_awareness`, `model_performance`, `attack_trends`.
- Analytics functions expose:
	- Logging predictions: `log_prediction()`.
	- Updating stats & patterns: `update_daily_statistics()` and `update_phishing_patterns()`.
	- Query functions: `get_analytics_data()` and `get_user_awareness_stats()`.

Notes: Simple schema is appropriate for prototype; migration/versioning or switching to an RDBMS would be needed for production scale.

## Tests & docs

- `README.md` contains quick-start and high-level notes (how-to: install, train, run, test).
- `test_predictor.py`:
	- Runs `src/train_from_csv.py` and then imports the predictor to make a single sample prediction. It is a functional/integration test.
- No dedicated unit tests for URL filtering, explainers, or analytics were found (only the integration test).

## Quick "try it locally" (PowerShell)

(From repo root)

```powershell
# create + activate venv (optional)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install deps
pip install -r requirements.txt

# train models (creates models/)
python src/train_from_csv.py

# run the Flask app
python app/app.py

# open http://localhost:5000
# or call detect endpoint with curl-like JSON:
# (PowerShell example)
$body = @{ email_text = "Your scholarship verification deadline is tomorrow. Click to verify account now." } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/detect -Method POST -Body $body -ContentType 'application/json'
```

## Quality gates (quick triage performed)

I ran a code compilation check across the repository to surface syntax errors.

- **Build / Syntax:** PASS
	- Action taken: `python -m compileall -q .` ran successfully with no syntax errors reported.
- **Lint / Typecheck:** NOT RUN
	- Recommendation: run `flake8` / `pylint` and `mypy` for type checking. There are dynamic patterns (joblib, pickled pipeline dicts) that may need type hints and small fixes.
- **Tests:** NOT RUN (not executed in this session)
	- Recommendation: run `pytest -q`. The provided test (`test_predictor.py`) will run training which takes a little time but is fast for the small synthetic dataset. Consider rewriting tests to avoid re-training (use pre-saved artifacts or mocks) for fast CI.

## Observations, risks & gaps

- Advanced detection & some features are disabled by default (see `FEATURES` in `config.py`): `advanced_detection_enabled=False`. The codebase has capability scaffolding for more advanced detection (threat intel, behavior analysis) which is currently inactive.
- Model management: artifacts are saved as pickles. No versioning, no model metadata, no reproducible training logs. Production-grade model registry or at least consistent naming & version metadata is recommended.
- Security: The API has no authentication, rate-limiting, or input sanitization beyond small checks — risky for public APIs.
- Email parsing: current pipeline expects `email_text` plain text. Complex multipart email parsing and attachment scanning is not implemented in the web API (training includes simple text).
- Network shortener resolution via runtime HTTP requests has been removed from this project to ensure deterministic, fast feature extraction and prediction. URL analysis relies only on static heuristics (domain checks, TLD lists, homograph detection, path patterns, and anchor mismatches).
- Tests re-train models; this slows CI. Prefer tests that mock or use precomputed artifacts to be faster and deterministic.
- Explainability is basic (keyword highlighting) — consider SHAP/LIME for model-level explanations.

## Suggested next steps (practical & prioritized)

1. **Enable a CI pipeline:**
	 - run `python -m compileall`, `pytest` (or tests that use prebuilt artifacts), `flake8`, and basic security checks.
2. **Fast tests:** add a set of unit tests that use a small pre-saved model artifact (store a tiny fixture in `tests/fixtures/`) instead of re-training in tests.
3. **Model management:** add model metadata (version, training data hash, metrics) and move to a model registry (MLflow or S3 + manifest) for production.
4. **Containerize:** add `Dockerfile` and `docker-compose.yml` for local/full-stack dev (app + optional DB persistence).
5. **Secure the API:** add authentication (API keys / basic auth), rate limiting and input size limits.
6. **Performance:** Move heavy ops (model loading, shortener resolution) out of request path or ensure caching and async resolve for shorteners.
7. **Observability:** Add structured logging, metrics (Prometheus), and error reporting.
8. **Improve ML:** Replace TF-IDF with modern embeddings (fine-tuned transformer or sentence embeddings), or maintain both for fallback. Add more robust features from attachments, headers and sender reputation.
9. **Explainability:** Add SHAP value computation for stacking classifier to give per-feature contribution.
10. **Data & privacy:** Ensure proper handling of sensitive fields, PII redaction, and opt-in telemetry for analytics.

---

All original content has been preserved and reorganized into clear sections and Markdown formatting for readability.