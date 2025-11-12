"""Compatibility wrapper providing higher-level detection helpers.

This file exposes:
- filter_urls: proxy to core.url_filter.filter_urls
- comprehensive_phishing_detection: a compact orchestration combining
  ML prediction + URL analysis + simple heuristics to produce a risk score
- get_user_education_tips, get_account_security_tips: proxies to education tips
"""
from typing import Dict, Any, List
from app.core.url_filter import filter_urls as core_filter_urls
from app.core.predictor import ModelBundle, predict_phishing
from app.modules.education.tips import get_user_education_tips, get_account_security_tips
from app.config import DETECTION_WEIGHTS


def filter_urls(email_text: str) -> Dict:
    """Proxy to core URL filtering so external code can use a single import."""
    return core_filter_urls(email_text)


def comprehensive_phishing_detection(email_text: str, headers: Dict[str, str] = None,
                                      attachments: List[str] = None, user_id: str = None) -> Dict[str, Any]:
    """Combine ML and URL heuristics into a single risk assessment.

    This is a compact, explainable orchestration intended for tests and
    higher-level demos. It is NOT a replacement for a full production
    pipeline, but provides a consistent API for the test-suite.
    """
    headers = headers or {}
    attachments = attachments or []

    bundle = ModelBundle()
    ml_out = predict_phishing(email_text, bundle)

    urls_out = core_filter_urls(email_text)

    # Convert ML confidence (0-1) to 0-100 scale
    ai_score = float(ml_out.get('confidence', 0.0)) * 100
    url_score = float(urls_out.get('overall_risk', 0.0))

    # Weights: use config if present, fallback to simple defaults
    w_ai = DETECTION_WEIGHTS.get('ai_ml', 0.6)
    w_url = 0.4 if w_ai == 0.6 else (1.0 - w_ai)

    overall = (w_ai * ai_score) + (w_url * url_score)

    # Attachments and suspicious headers increase risk slightly
    if attachments:
        overall += min(10 * len(attachments), 20)

    # Normalize to 0-100
    overall = max(0.0, min(100.0, overall))

    if overall >= 70:
        risk_level = 'HIGH'
    elif overall >= 40:
        risk_level = 'MEDIUM'
    elif overall >= 10:
        risk_level = 'LOW'
    else:
        risk_level = 'SAFE'

    recommendations = []
    if risk_level == 'HIGH':
        recommendations = [
            'Quarantine the email and do not click links or open attachments.',
            'Reset passwords if you submitted credentials recently.',
            'Report the email to the security team and block sender if confirmed malicious.'
        ]
    elif risk_level == 'MEDIUM':
        recommendations = [
            'Do not click links until verifying sender identity.',
            'Hover over links to inspect destinations; do not provide credentials.',
        ]
    else:
        recommendations = [
            'Monitor the email but no immediate action required.',
            'Educate the recipient about safe email practices.'
        ]

    return {
        'risk_level': risk_level,
        'overall_risk_score': round(overall, 2),
        'ml_output': ml_out,
        'url_output': urls_out,
        'recommendations': recommendations
    }


__all__ = [
    'filter_urls',
    'comprehensive_phishing_detection',
    'get_user_education_tips',
    'get_account_security_tips'
]
