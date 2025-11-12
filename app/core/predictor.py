"""Predictor utilities: load models and provide prediction API."""
from pathlib import Path
import joblib
import re
import numpy as np
from typing import Dict, Any
from app.config import MODEL_FILES, MODEL_WEIGHTS

# Expanded academic keyword list with more phishing indicators
ACADEMIC_KEYWORDS = [
    'scholarship','exam','fee','admission','certificate','deadline',
    'registration','result','verification','urgent','update','verify',
    'account', 'credentials', 'password', 'confirm', 'approve', 'approve',
    'claim', 'grant', 'disbursement', 'internship', 'alert', 'suspend'
]

# Phishing indicators - common phishing email patterns
PHISHING_INDICATORS = {
    'verify_account': r'verify.*account|confirm.*account|validate.*account',
    'urgent_action': r'urgent|immediately|today|right now|asap|act now',
    'suspicious_links': r'click\s+here|click.*link|click.*below|confirm.*link',
    'credential_request': r'provide.*password|enter.*credentials|confirm.*identity|banking details',
    'threat_language': r'expire|suspend|deactivate|delete|locked|compromised',
    'too_good': r'congratulations|approved|eligible|won|refund|reward',
}


class ModelBundle:
    """Container for ML models used in phishing detection."""
    
    def __init__(self, root: Path = None):
        """Load trained models from disk.
        
        Args:
            root: Project root path. If None, uses config.
        """
        if root is None:
            # Prefer a single saved pipeline if available (helper pipeline dict)
            try:
                # New pipeline is saved as a dict with 'vectorizer' and 'stacking'
                self.pipeline = joblib.load(MODEL_FILES['pipeline'])
                # If pipeline is a dict, extract components for faster access
                if isinstance(self.pipeline, dict):
                    self.vectorizer = self.pipeline.get('vectorizer')
                    self.stacking = self.pipeline.get('stacking')
                else:
                    # Old behaviour: pipeline might be a Pipeline object
                    self.vectorizer = None
                    self.stacking = None
            except Exception:
                self.pipeline = None
                self.vectorizer = None
                self.stacking = None

            # Backwards-compatible loading of separate artifacts if pipeline not present
            if self.pipeline is None:
                try:
                    self.vectorizer = joblib.load(MODEL_FILES['vectorizer'])
                except Exception:
                    self.vectorizer = None

                try:
                    self.lr = joblib.load(MODEL_FILES['logistic'])
                except Exception:
                    self.lr = None

                try:
                    self.nb = joblib.load(MODEL_FILES['naive_bayes'])
                except Exception:
                    self.nb = None

                try:
                    self.svm = joblib.load(MODEL_FILES['svm'])
                except Exception:
                    self.svm = None
        else:
            # Legacy path-based loading
            models_dir = root / 'models'
            self.vectorizer = joblib.load(models_dir / 'tfidf.pkl')
            self.lr = joblib.load(models_dir / 'logistic.pkl')
            self.nb = joblib.load(models_dir / 'nb.pkl')
            try:
                self.svm = joblib.load(models_dir / 'svm.pkl')
            except:
                self.svm = None


def calculate_urgency_score(text: str) -> float:
    """Calculate urgency score based on keyword frequency and intensity."""
    urgency_keywords = {
        'urgent': 10, 'immediate': 9, 'asap': 9,
        'deadline': 8, 'expires': 8, 'act now': 9,
        'limited time': 8, 'hurry': 8, 'immediately': 9,
        'today': 7, 'now': 7, 'must': 6, 'right now': 10,
        'final notice': 10, 'last chance': 9
    }
    text_lower = text.lower()
    urgency_score = 0
    keyword_count = 0
    for keyword, weight in urgency_keywords.items():
        count = text_lower.count(keyword)
        if count:
            urgency_score += count * weight
            keyword_count += count
    urgency_score = min(urgency_score / max(keyword_count, 1), 10)
    return float(urgency_score)


def extract_academic_keywords(text: str):
    """Extract academic keywords found in text."""
    text_lower = text.lower()
    found = []
    for kw in ACADEMIC_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            found.append(kw)
    return found


def calculate_phishing_indicators_score(text: str) -> float:
    """Score based on presence of known phishing indicators."""
    text_lower = text.lower()
    indicator_count = 0
    max_indicators = len(PHISHING_INDICATORS)
    
    for indicator_name, pattern in PHISHING_INDICATORS.items():
        if re.search(pattern, text_lower):
            indicator_count += 1
    
    return (indicator_count / max_indicators) * 10


def predict_phishing(email_text: str, bundle: ModelBundle, headers: Dict[str, str] = None, attachments: list = None) -> Dict[str, Any]:
    """Return classification, confidence (0-1), urgency_score, keywords, and model probs.
    
    Uses an ensemble of multiple models with improved decision logic.
    """
    headers = headers or {}
    attachments = attachments or []
    # If a full pipeline (tfidf + stacking) is available, use it for prediction
    model_probs = {}
    model_scores = []
    ensemble_score = 0.0

    if getattr(bundle, 'pipeline', None) is not None:
        try:
            # If pipeline is a helper dict (vectorizer + stacking), use vectorizer
            if isinstance(bundle.pipeline, dict):
                vec = bundle.pipeline['vectorizer'].transform([email_text])
                # compute url features and append to TF-IDF at predict time
                try:
                    from app.core.url_filter import url_features_from_text
                    import numpy as _np
                    from scipy.sparse import csr_matrix as _csr

                    url_feats = _np.array([url_features_from_text(email_text)], dtype=float)
                    url_sparse = _csr(url_feats)
                    vec = _np.hstack([vec.toarray(), url_feats])
                    # convert back to 2D array for stacking predict_proba
                except Exception:
                    # If URL features or scipy unavailable, fall back to TF-IDF only
                    pass

                # Use stacking model saved under helper pipeline
                try:
                    prob = float(bundle.pipeline['stacking'].predict_proba(vec)[0][1])
                    model_probs['pipeline'] = prob
                    model_scores = [prob]
                    ensemble_score = prob
                except Exception:
                    ensemble_score = 0.0
                    model_probs = {}
                    model_scores = []
            else:
                # If pipeline is a sklearn Pipeline object, use its predict_proba
                prob = float(bundle.pipeline.predict_proba([email_text])[0][1])
                model_probs['pipeline'] = prob
                model_scores = [prob]
                ensemble_score = prob
        except Exception:
            # Fallback to older artifacts if pipeline predict_proba fails
            ensemble_score = 0.0
            model_probs = {}
            model_scores = []

    # Fallback: if no pipeline, use legacy vectorizer + individual models
    if ensemble_score == 0.0 and getattr(bundle, 'vectorizer', None) is not None:
        vec = bundle.vectorizer.transform([email_text])
        try:
            if bundle.lr is not None:
                lr_prob = bundle.lr.predict_proba(vec)[0][1]
                model_probs['logistic'] = float(lr_prob)
                model_scores.append(lr_prob)
        except Exception:
            pass

        try:
            if bundle.nb is not None:
                nb_prob = bundle.nb.predict_proba(vec)[0][1]
                model_probs['nb'] = float(nb_prob)
                model_scores.append(nb_prob)
        except Exception:
            pass

        try:
            if bundle.svm is not None:
                svm_score = bundle.svm.decision_function(vec)[0]
                svm_prob = 1 / (1 + np.exp(-svm_score))
                model_probs['svm'] = float(svm_prob)
                model_scores.append(svm_prob)
        except Exception:
            pass

        if model_scores:
            ensemble_score = sum(model_scores) / len(model_scores)

    # Calculate additional features
    urgency = calculate_urgency_score(email_text)
    phishing_indicators = calculate_phishing_indicators_score(email_text)
    keywords = extract_academic_keywords(email_text)

    # Header-based simple features
    def header_features(hdrs: Dict[str, str]):
        spf = 0.0
        dkim = 0.0
        dmarc = 0.0
        if not hdrs:
            return [spf, dkim, dmarc]
        auth = hdrs.get('Authentication-Results', '') or hdrs.get('Authentication-Results:', '')
        auth_low = auth.lower()
        if 'spf=pass' in auth_low:
            spf = 1.0
        if 'dkim=pass' in auth_low:
            dkim = 1.0
        if 'dmarc=pass' in auth_low:
            dmarc = 1.0
        return [spf, dkim, dmarc]

    hdr_feats = header_features(headers)

    # Header-derived risk (0-1) higher when SPF/DKIM/DMARC are missing or failing
    header_risk = 0.0
    try:
        header_risk = 1.0 - (sum(hdr_feats) / max(1.0, len(hdr_feats)))
    except Exception:
        header_risk = 0.0

    # Enhanced final score calculation with better weighting
    # - 55% from ML models (most important)
    # - 20% from phishing indicators (strong signal)
    # - 15% from urgency (contextual)
    # - 10% from header signals (spf/dkim/dmarc)
    final_score = (
        0.55 * ensemble_score +
        0.20 * (phishing_indicators / 10) +
        0.15 * (urgency / 10) +
        0.10 * header_risk
    )
    
    classification = 'PHISHING' if final_score >= 0.5 else 'LEGITIMATE'

    return {
        'classification': classification,
        'confidence': float(final_score),
        'model_probs': model_probs,
        'urgency_score': float(urgency),
        'phishing_indicators_score': float(phishing_indicators),
        'keywords': keywords,
        'ensemble_score': float(ensemble_score)
    }
