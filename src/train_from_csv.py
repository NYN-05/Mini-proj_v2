"""Train models using the project's primary CSV dataset: `Phishing_Email.csv`.

This script trains the TF-IDF + URL feature + stacking classifier pipeline
using the single authoritative dataset `Phishing_Email.csv` located at the
project root. The CSV should contain an email text column (commonly
`Email Text`) and a type/label column (commonly `Email Type`). The script
normalizes those to `text` and `label` before training and saves artifacts
to the `models/` directory.
"""
import os
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import StackingClassifier
from sklearn.metrics import classification_report, roc_auc_score
from scipy.sparse import csr_matrix, hstack

import sys
import argparse
import time

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core import url_features_from_text
import numpy as np


def ensure_models_dir(root: Path):
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def load_csv_dataset(root: Path) -> pd.DataFrame:
    # Only load the single canonical CSV at project root: Phishing_Email.csv
    csv_file = root / 'Phishing_Email.csv'
    if csv_file.exists():
        print(f"Loading dataset from: {csv_file}")
        df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)
    else:
        raise FileNotFoundError('No dataset found. Place CSV at project root named `Phishing_Email.csv`.')
    # Try to normalize common variants: 'Email Text' -> 'text', 'Email Type' -> 'label'
    if 'Email Text' in df.columns and 'text' not in df.columns:
        df = df.rename(columns={'Email Text': 'text'})
    if 'Email Type' in df.columns and 'label' not in df.columns:
        # Map values like 'Phishing Email' to 1, others to 0
        df['label'] = df['Email Type'].apply(lambda v: 1 if isinstance(v, str) and 'phish' in v.lower() else 0)
    # If there is a column named 'Email', map it to 'text'
    if 'text' not in df.columns and 'Email' in df.columns:
        df = df.rename(columns={'Email': 'text'})

    # Ensure expected columns
    if 'text' not in df.columns or 'label' not in df.columns:
        raise ValueError('Dataset must contain columns named `text` and `label` (provide `Phishing_Email.csv` with `Email Text`/`Email Type` or `text`/`label` columns)')

    # Clean rows
    df = df[['text', 'label']].dropna()
    # Ensure label numeric
    df['label'] = pd.to_numeric(df['label'], errors='coerce').fillna(0).astype(int)
    return df


def train_and_save(root: Path,
                   sample_frac: float = 1.0,
                   tfidf_max_features: int = 2000,
                   ngram_range=(1, 2),
                   cv_folds: int = 3,
                   calibrate_svm: bool = False,
                   n_jobs: int = -1):
    """Train models and save artifacts.

    Parameters tuned for faster default runs: lower max_features, smaller ngram range,
    fewer CV folds, and optional SVM calibration.
    """
    start_time = time.time()
    df = load_csv_dataset(root)

    # Optionally sample for fast iterations
    if 0 < sample_frac < 1.0:
        df = df.sample(frac=sample_frac, random_state=42).reset_index(drop=True)

    print(f"Dataset size: {len(df)} samples ({df['label'].sum()} phishing, {(df['label']==0).sum()} legitimate)")

    # Vectorizer (configurable to reduce runtime)
    vectorizer = TfidfVectorizer(
        max_features=tfidf_max_features,
        ngram_range=ngram_range,
        min_df=1,
        max_df=0.95,
        lowercase=True,
        stop_words='english'
    )

    X_tfidf = vectorizer.fit_transform(df['text'])
    y = df['label'].values

    # URL features (fast)
    url_feat_list = [url_features_from_text(t) for t in df['text']]
    url_feats = np.array(url_feat_list, dtype=float)
    url_sparse = csr_matrix(url_feats)
    X = hstack([X_tfidf, url_sparse], format='csr')

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(set(y))>1 else None)

    lr = LogisticRegression(max_iter=1000, C=0.1, class_weight='balanced', solver='lbfgs')
    nb = MultinomialNB(alpha=0.1)
    base_svm = LinearSVC(max_iter=2000, C=0.1, class_weight='balanced', random_state=42, dual=False)

    # Optionally calibrate SVM (costly). If disabled, use raw LinearSVC in stacking.
    if calibrate_svm:
        calibrated_svm = CalibratedClassifierCV(base_svm, cv=max(2, cv_folds))
        svm_estimator = ('svm', calibrated_svm)
    else:
        svm_estimator = ('svm', base_svm)

    stacking = StackingClassifier(
        estimators=[('lr', lr), ('nb', nb), svm_estimator],
        final_estimator=LogisticRegression(max_iter=1000),
        cv=max(2, cv_folds),
        passthrough=True,
        n_jobs=n_jobs,
        verbose=1
    )

    print('[Fitting] Training stacking classifier...')
    stacking.fit(X_train, y_train)

    y_pred = stacking.predict(X_test)
    try:
        y_proba = stacking.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba)
    except Exception:
        y_proba = None
        auc = None

    print('\n=== Holdout Evaluation (stacking) ===')
    print(classification_report(y_test, y_pred))
    if auc is not None:
        print(f"ROC AUC: {auc:.4f}")

    models_dir = ensure_models_dir(root)
    joblib.dump(vectorizer, models_dir / "tfidf.pkl")
    joblib.dump(lr, models_dir / "logistic.pkl")
    joblib.dump(nb, models_dir / "nb.pkl")
    # Save base_svm or calibrated_svm accordingly
    if calibrate_svm:
        joblib.dump(calibrated_svm, models_dir / "svm.pkl")
    else:
        joblib.dump(base_svm, models_dir / "svm.pkl")
    joblib.dump(stacking, models_dir / "stacking.pkl")

    helper_pipeline = {'vectorizer': vectorizer, 'stacking': stacking}
    joblib.dump(helper_pipeline, models_dir / "pipeline.pkl")

    elapsed = time.time() - start_time
    print(f"\nSaved models to: {models_dir}")
    print(f"Total training time: {elapsed:.1f} seconds")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train phishing models from CSV (fast defaults).')
    parser.add_argument('--sample-frac', type=float, default=1.0,
                        help='Fraction of dataset to sample for quick runs (0.0-1.0)')
    parser.add_argument('--tfidf-max-features', type=int, default=2000,
                        help='Max features for TF-IDF (reduce for speed)')
    parser.add_argument('--ngram-min', type=int, default=1, help='TF-IDF ngram min')
    parser.add_argument('--ngram-max', type=int, default=2, help='TF-IDF ngram max')
    parser.add_argument('--cv-folds', type=int, default=3, help='Number of CV folds for stacking')
    parser.add_argument('--calibrate-svm', action='store_true', help='Calibrate SVM (slower)')
    parser.add_argument('--n-jobs', type=int, default=-1, help='n_jobs for parallel training')
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    ngram = (args.ngram_min, args.ngram_max)
    train_and_save(root,
                   sample_frac=args.sample_frac,
                   tfidf_max_features=args.tfidf_max_features,
                   ngram_range=ngram,
                   cv_folds=args.cv_folds,
                   calibrate_svm=args.calibrate_svm,
                   n_jobs=args.n_jobs)
