"""Core detection module initialization.

This module re-exports the consolidated `app.detector` helpers so other
modules can continue to import from `app.core` without changes.
"""
from app.detector import (
    ModelBundle,
    predict_phishing,
    highlight_keywords,
    risk_factors_from_prediction,
    filter_urls,
    get_url_risk_summary,
    analyze_single_url,
    extract_urls,
    url_features_from_text,
    # word-level analyzer
    word_level_analysis,
)

__all__ = [
    'ModelBundle',
    'predict_phishing',
    'highlight_keywords',
    'risk_factors_from_prediction',
    'filter_urls',
    'get_url_risk_summary',
    'analyze_single_url',
    'extract_urls',
    'url_features_from_text',
    'word_level_analysis',
]
