"""Lightweight analytics DB shim.

This file provides minimal stub implementations so the analytics
module can be imported even when a full SQLite implementation is
not present. Functions are no-ops or return simple defaults. This
prevents ImportError at app startup while preserving call sites.
"""
from typing import Any, Dict, List


def init_db(db_path: str = None) -> None:
    """Initialize analytics DB (noop placeholder)."""
    return None


def log_prediction(**kwargs) -> None:
    """Log a prediction. Real implementation should persist to DB.

    This placeholder accepts arbitrary keyword args and does nothing.
    """
    return None


def get_analytics_data(institution: str = None, days: int = 7) -> Dict[str, Any]:
    """Return minimal analytics payload (placeholder)."""
    return {
        'institution': institution or 'unknown',
        'days': days,
        'total_predictions': 0,
        'phishing_count': 0,
        'legitimate_count': 0,
    }


def update_daily_statistics(institution: str = None) -> None:
    """Update daily stats (noop placeholder)."""
    return None


def update_phishing_patterns(classification: str = None, confidence: float = 0.0, keywords: List[str] = None, institution: str = None) -> None:
    """Update pattern store (noop placeholder)."""
    return None


def get_user_awareness_stats(institution: str = None) -> Dict[str, Any]:
    """Return placeholder user awareness stats."""
    return {'institution': institution or 'unknown', 'awareness_score': None}


def get_attack_heatmap(institution: str = None, days: int = 7) -> List[Any]:
    """Return placeholder heatmap data."""
    return []
