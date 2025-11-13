"""DEPRECATED: proxy to consolidated `app.detector`.

This module is preserved for compatibility. Consumers should import
from `app.core` (re-exported) or `app.detector` directly.
"""

from app.detector import ModelBundle, predict_phishing

__all__ = ['ModelBundle', 'predict_phishing']
