"""
Combined detector module.

This file consolidates ML predictor, URL filtering and explainability
helpers from the original `app/core` submodules into a single module to
simplify the project layout while keeping the existing public API.
"""
from pathlib import Path
import os
import joblib
import re
import numpy as np
from typing import Dict, Any, List
import unicodedata
import html
from urllib.parse import urlparse
from scipy.sparse import csr_matrix

from app.config import MODEL_FILES, SUSPICIOUS_TLDS, URL_SHORTENERS
from app.utils.emotional_analyzer import analyze_emotional_tone

# ----------------------------- Predictor ---------------------------------

ACADEMIC_KEYWORDS = [
    'scholarship','exam','fee','admission','certificate','deadline',
    'registration','result','verification','urgent','update','verify',
    'account', 'credentials', 'password', 'confirm', 'approve',
    'claim', 'grant', 'disbursement', 'internship', 'alert', 'suspend'
]

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
        if root is None:
            try:
                self.pipeline = joblib.load(MODEL_FILES['pipeline'])
                if isinstance(self.pipeline, dict):
                    self.vectorizer = self.pipeline.get('vectorizer')
                    self.stacking = self.pipeline.get('stacking')
                else:
                    self.vectorizer = None
                    self.stacking = None
            except Exception:
                self.pipeline = None
                self.vectorizer = None
                self.stacking = None

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
            models_dir = root / 'models'
            self.vectorizer = joblib.load(models_dir / 'tfidf.pkl')
            self.lr = joblib.load(models_dir / 'logistic.pkl')
            self.nb = joblib.load(models_dir / 'nb.pkl')
            try:
                self.svm = joblib.load(models_dir / 'svm.pkl')
            except Exception:
                self.svm = None


def calculate_urgency_score(text: str) -> float:
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
    text_lower = text.lower()
    found = []
    for kw in ACADEMIC_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            found.append(kw)
    return found


def calculate_phishing_indicators_score(text: str) -> float:
    text_lower = text.lower()
    indicator_count = 0
    max_indicators = len(PHISHING_INDICATORS)
    for indicator_name, pattern in PHISHING_INDICATORS.items():
        if re.search(pattern, text_lower):
            indicator_count += 1
    return (indicator_count / max_indicators) * 10


def predict_phishing(email_text: str, bundle: ModelBundle, headers: Dict[str, str] = None, attachments: list = None) -> Dict[str, Any]:
    headers = headers or {}
    attachments = attachments or []
    model_probs = {}
    model_scores = []
    ensemble_score = 0.0

    if getattr(bundle, 'pipeline', None) is not None:
        try:
            if isinstance(bundle.pipeline, dict):
                vec = bundle.pipeline['vectorizer'].transform([email_text])
                try:
                    url_feats = np.array([url_features_from_text(email_text)], dtype=float)
                    vec = np.hstack([vec.toarray(), url_feats])
                except Exception:
                    pass
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
                prob = float(bundle.pipeline.predict_proba([email_text])[0][1])
                model_probs['pipeline'] = prob
                model_scores = [prob]
                ensemble_score = prob
        except Exception:
            ensemble_score = 0.0
            model_probs = {}
            model_scores = []

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

    urgency = calculate_urgency_score(email_text)
    phishing_indicators = calculate_phishing_indicators_score(email_text)
    keywords = extract_academic_keywords(email_text)

    # Emotional tone analysis for social engineering detection
    emotional_analysis = analyze_emotional_tone(email_text)
    emotional_risk = emotional_analysis['hidden_meaning_score'] / 100.0  # Normalize to 0-1

    # Get URL risk analysis
    urls = extract_urls(email_text)
    url_risk = 0.0
    if urls:
        for url in urls:
            if is_url_shortener(url) or has_suspicious_tld(url) or is_ip_address_url(url):
                url_risk = 1.0
                break
            if check_suspicious_path(url):
                url_risk = max(url_risk, 0.7)

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
    header_risk = 0.0
    try:
        header_risk = 1.0 - (sum(hdr_feats) / max(1.0, len(hdr_feats)))
    except Exception:
        header_risk = 0.0

    # Enhanced scoring with emotional tone analysis
    # Weights: ensemble 0.35, emotional 0.20, indicators 0.20, urgency 0.15, header 0.05, url 0.05
    # Emotional analysis gets significant weight as it captures social engineering tactics
    final_score = (
        0.35 * ensemble_score +
        0.20 * emotional_risk +
        0.20 * (phishing_indicators / 10) +
        0.15 * (urgency / 10) +
        0.05 * header_risk +
        0.05 * url_risk
    )

    # Threshold remains 0.45 to catch more phishing with improved emotional detection
    classification = 'PHISHING' if final_score >= 0.45 else 'LEGITIMATE'

    return {
        'classification': classification,
        'confidence': float(final_score),
        'model_probs': model_probs,
        'urgency_score': float(urgency),
        'phishing_indicators_score': float(phishing_indicators),
        'keywords': keywords,
        'ensemble_score': float(ensemble_score),
        'emotional_analysis': emotional_analysis
    }


# --------------------------- URL Filtering -------------------------------

def extract_urls(text: str) -> List[str]:
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    www_pattern = r'www\\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    www_urls = re.findall(www_pattern, text, re.IGNORECASE)
    urls.extend(['http://' + url for url in www_urls])
    return list(set(urls))


def is_ip_address_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path.split('/')[0]
        ip_pattern = r'^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$'
        return bool(re.match(ip_pattern, hostname))
    except Exception:
        return False


def is_url_shortener(url: str) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(shortener in domain for shortener in URL_SHORTENERS)
    except Exception:
        return False


def has_suspicious_tld(url: str) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS)
    except Exception:
        return False


def check_homograph_attack(url: str) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        if not domain:
            return False
        if domain.startswith('xn--') or '.xn--' in domain:
            return True
        norm = unicodedata.normalize('NFKC', domain)
        if all(ord(c) < 128 for c in norm):
            return False
        scripts = set()
        for ch in norm:
            if ord(ch) < 128:
                scripts.add('ASCII')
                continue
            try:
                name = unicodedata.name(ch)
                block = name.split(' ')[0]
                scripts.add(block)
            except ValueError:
                scripts.add('UNKNOWN')
        return len(scripts) > 1
    except Exception:
        return False


def resolve_shortener(url: str, timeout: float = 3.0) -> str:
    # Network resolution removed: simply return the input URL. This avoids
    # per-URL HTTP calls during feature extraction or prediction which can
    # block training or slow down inference.
    return url


def has_excessive_subdomains(url: str, threshold: int = 3) -> bool:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        subdomain_count = domain.count('.')
        return subdomain_count > threshold
    except Exception:
        return False


def check_suspicious_path(url: str) -> bool:
    suspicious_patterns = [
        'login', 'signin', 'verify', 'account', 'update',
        'confirm', 'secure', 'banking', 'paypal', 'ebay',
        'amazon', 'suspended', 'locked', 'unusual'
    ]
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        full_path = path + query
        return any(pattern in full_path for pattern in suspicious_patterns)
    except Exception:
        return False


def analyze_single_url(url: str) -> Dict:
    issues = []
    risk_score = 0
    if is_ip_address_url(url):
        issues.append('Uses IP address instead of domain name')
        risk_score += 30
    if is_url_shortener(url):
        issues.append('Uses URL shortening service')
        risk_score += 25
    if has_suspicious_tld(url):
        issues.append('Uses suspicious top-level domain')
        risk_score += 20
    resolved = resolve_shortener(url)
    url_to_check = resolved if resolved and resolved != url else url
    if check_homograph_attack(url_to_check):
        issues.append('Contains lookalike characters (homograph attack)')
        risk_score += 35
    if has_excessive_subdomains(url):
        issues.append('Has excessive number of subdomains')
        risk_score += 15
    if check_suspicious_path(url):
        issues.append('Path contains suspicious keywords')
        risk_score += 10
    if risk_score >= 50:
        risk_level = 'HIGH'
    elif risk_score >= 30:
        risk_level = 'MEDIUM'
    elif risk_score >= 10:
        risk_level = 'LOW'
    else:
        risk_level = 'SAFE'
    return {
        'url': url,
        'risk_score': min(risk_score, 100),
        'risk_level': risk_level,
        'issues': issues
    }


def filter_urls(email_text: str) -> Dict:
    urls = extract_urls(email_text)
    if not urls:
        return {
            'urls_found': 0,
            'urls': [],
            'high_risk_urls': [],
            'medium_risk_urls': [],
            'overall_risk': 0,
            'has_suspicious_urls': False
        }
    url_analyses = [analyze_single_url(url) for url in urls]
    high_risk = [u for u in url_analyses if u['risk_level'] == 'HIGH']
    medium_risk = [u for u in url_analyses if u['risk_level'] == 'MEDIUM']
    overall_risk = sum(u['risk_score'] for u in url_analyses) / len(url_analyses) if url_analyses else 0
    return {
        'urls_found': len(urls),
        'urls': url_analyses,
        'high_risk_urls': high_risk,
        'medium_risk_urls': medium_risk,
        'overall_risk': round(overall_risk, 2),
        'has_suspicious_urls': len(high_risk) > 0 or len(medium_risk) > 0
    }


def get_url_risk_summary(url_analysis: Dict) -> List[str]:
    risk_factors = []
    if url_analysis['urls_found'] == 0:
        return ['No URLs detected in email']
    risk_factors.append(f"Found {url_analysis['urls_found']} URL(s) in email")
    if url_analysis['high_risk_urls']:
        risk_factors.append(f"⚠️ {len(url_analysis['high_risk_urls'])} HIGH RISK URL(s) detected")
        for url_info in url_analysis['high_risk_urls']:
            risk_factors.append(f"  - {url_info['url']}: {', '.join(url_info['issues'])}")
    if url_analysis['medium_risk_urls']:
        risk_factors.append(f"⚠️ {len(url_analysis['medium_risk_urls'])} MEDIUM RISK URL(s) detected")
        for url_info in url_analysis['medium_risk_urls']:
            risk_factors.append(f"  - {url_info['url']}: {', '.join(url_info['issues'])}")
    if url_analysis['overall_risk'] >= 30:
        risk_factors.append(f"Overall URL risk score: {url_analysis['overall_risk']}/100")
    return risk_factors


def url_features_from_text(text: str) -> List[float]:
    urls = extract_urls(text)
    if not urls:
        return [0.0] * 8
    shortener_flag = 0
    ip_flag = 0
    suspicious_tld_count = 0
    homograph_count = 0
    subdomain_counts = []
    path_suspicious_count = 0
    for url in urls:
        if is_url_shortener(url):
            shortener_flag = 1
        if is_ip_address_url(url):
            ip_flag = 1
        final_url = resolve_shortener(url)
        if has_suspicious_tld(final_url):
            suspicious_tld_count += 1
        if check_homograph_attack(final_url):
            homograph_count += 1
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            subdomain_counts.append(domain.count('.'))
            if check_suspicious_path(url):
                path_suspicious_count += 1
        except Exception:
            subdomain_counts.append(0)
    avg_subdomains = float(sum(subdomain_counts) / max(1, len(subdomain_counts)))
    anchor_mismatch = 0
    try:
        anchors = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, flags=re.IGNORECASE | re.DOTALL)
        for href, display in anchors:
            href_domain = urlparse(href).netloc
            display_unescaped = html.unescape(display)
            found = re.search(r'(https?://)?([\w\.-]+\.[a-zA-Z]{2,})', display_unescaped)
            if found:
                disp_domain = found.group(2).lower()
                if href_domain and disp_domain and disp_domain not in href_domain.lower():
                    anchor_mismatch += 1
    except Exception:
        anchor_mismatch = 0
    return [
        float(shortener_flag),
        float(ip_flag),
        float(suspicious_tld_count),
        float(homograph_count),
        float(avg_subdomains),
        float(path_suspicious_count),
        float(len(urls)),
        float(anchor_mismatch)
    ]


# --------------------------- Explainability -----------------------------

def highlight_keywords(text: str, keywords: List[str]) -> str:
    if not keywords:
        return html.escape(text)
    escaped = html.escape(text)
    out = escaped
    for kw in sorted(set(keywords), key=len, reverse=True):
        out = out.replace(kw, f"<span class=\"risk-high\">{kw}</span>")
        out = out.replace(kw.capitalize(), f"<span class=\"risk-high\">{kw.capitalize()}</span>")
    return out


def risk_factors_from_prediction(pred: Dict) -> List[str]:
    factors = []
    if pred.get('keywords'):
        factors.append(f"High-risk keywords: {', '.join(pred['keywords'])}")
    if pred.get('urgency_score', 0) >= 6:
        factors.append(f"Urgency detected (score {pred['urgency_score']}/10)")
    if pred.get('model_probs'):
        lp = pred['model_probs'].get('logistic', 0)
        npb = pred['model_probs'].get('nb', 0)
        factors.append(f"Model agreement: logistic={lp:.2f}, nb={npb:.2f}")
    return factors


# ------------------------- Word-level Analysis -------------------------
def word_level_analysis(text: str, bundle: ModelBundle = None) -> List[Dict[str, Any]]:
    """Analyze text token-by-token and return per-word indicators.

    For each token we return a small set of heuristic flags plus an
    optional model probability when a model/vectorizer is available.
    This performs only local, inexpensive operations; model probability
    estimation is attempted but will silently be skipped on error.
    """
    # Token regex: include letters, numbers and common punctuation used in URLs/emails
    tokens = re.findall(r"\b[0-9A-Za-z@./:%+\-']+\b", text)
    word_info = []

    # Small urgency keyword set reused from calculate_urgency_score
    urgency_keys = set([
        'urgent', 'immediate', 'asap', 'deadline', 'expires', 'act', 'now',
        'hurry', 'immediately', 'today', 'must'
    ])

    for tok in tokens:
        info = {
            'token': tok,
            'lower': tok.lower(),
            'is_url': False,
            'is_email': False,
            'is_academic_kw': False,
            'indicator_matches': [],
            'urgency': False,
            'contains_digits': any(ch.isdigit() for ch in tok),
            'model_prob': None,
            'model_probs': {}
        }

        low = info['lower']

        # URL and email detection
        if re.match(r'^https?://', tok, flags=re.IGNORECASE) or tok.startswith('www.'):
            info['is_url'] = True
        if re.match(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}', tok):
            info['is_email'] = True

        # Academic keyword
        if low in (kw.lower() for kw in ACADEMIC_KEYWORDS):
            info['is_academic_kw'] = True

        # Indicator pattern matches (per-word check using simple search)
        for name, pattern in PHISHING_INDICATORS.items():
            try:
                if re.search(pattern, low):
                    info['indicator_matches'].append(name)
            except Exception:
                pass

        # Urgency token
        if any(uk == low or uk in low for uk in urgency_keys):
            info['urgency'] = True

        # Attempt to get model-level probability for this token
        try:
            if bundle is not None:
                # Prefer pipeline if available
                if getattr(bundle, 'pipeline', None) is not None:
                    try:
                        if isinstance(bundle.pipeline, dict) and bundle.pipeline.get('vectorizer'):
                            vec = bundle.pipeline['vectorizer'].transform([tok])
                            # Some pipelines expect extra URL features; skip if incompatible
                            try:
                                prob = float(bundle.pipeline['stacking'].predict_proba(vec)[0][1])
                                info['model_prob'] = prob
                                info['model_probs']['pipeline'] = prob
                            except Exception:
                                # Try pipeline object interface
                                try:
                                    prob = float(bundle.pipeline.predict_proba([tok])[0][1])
                                    info['model_prob'] = prob
                                    info['model_probs']['pipeline'] = prob
                                except Exception:
                                    pass
                        else:
                            # Direct pipeline object
                            try:
                                prob = float(bundle.pipeline.predict_proba([tok])[0][1])
                                info['model_prob'] = prob
                                info['model_probs']['pipeline'] = prob
                            except Exception:
                                pass
                    except Exception:
                        pass

                # Fallback to individual models + vectorizer
                if info['model_prob'] is None and getattr(bundle, 'vectorizer', None) is not None:
                    vec = bundle.vectorizer.transform([tok])
                    probs = []
                    try:
                        if getattr(bundle, 'lr', None) is not None:
                            lr_p = float(bundle.lr.predict_proba(vec)[0][1])
                            info['model_probs']['logistic'] = lr_p
                            probs.append(lr_p)
                    except Exception:
                        pass
                    try:
                        if getattr(bundle, 'nb', None) is not None:
                            nb_p = float(bundle.nb.predict_proba(vec)[0][1])
                            info['model_probs']['nb'] = nb_p
                            probs.append(nb_p)
                    except Exception:
                        pass
                    try:
                        if getattr(bundle, 'svm', None) is not None:
                            svm_score = bundle.svm.decision_function(vec)[0]
                            svm_p = 1 / (1 + np.exp(-svm_score))
                            info['model_probs']['svm'] = float(svm_p)
                            probs.append(svm_p)
                    except Exception:
                        pass
                    if probs:
                        info['model_prob'] = float(sum(probs) / len(probs))
        except Exception:
            # Keep tokens even if model probing fails
            pass

        word_info.append(info)

    return word_info
