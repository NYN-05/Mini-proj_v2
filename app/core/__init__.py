"""Core detection module initialization."""
from .predictor import ModelBundle, predict_phishing
from .explainer import highlight_keywords, risk_factors_from_prediction
from .url_filter import filter_urls, get_url_risk_summary, analyze_single_url, extract_urls

__all__ = [
    'ModelBundle', 
    'predict_phishing', 
    'highlight_keywords', 
    'risk_factors_from_prediction',
    'filter_urls',
    'get_url_risk_summary',
    'analyze_single_url',
    'extract_urls'
]
