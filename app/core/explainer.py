"""Explainability helpers: highlight keywords and produce risk factors.

This module no longer hard-codes CSS classes, tag names, or thresholds.
Instead it reads `EXPLAINER_CONFIG` from `app.config` so values are centralized.
"""
from typing import List, Dict
import html
import re

from app.config import EXPLAINER_CONFIG


def highlight_keywords(text: str, keywords: List[str]) -> str:
    """Return HTML where keywords are wrapped in configured tag/class.

    - Escapes HTML by default (configurable).
    - Uses case-insensitive, word-boundary matching and preserves original casing.
    """
    if not keywords:
        return html.escape(text) if EXPLAINER_CONFIG.get('escape_html', True) else text

    out = html.escape(text) if EXPLAINER_CONFIG.get('escape_html', True) else text

    tag = EXPLAINER_CONFIG.get('highlight_tag', 'span')
    css_class = EXPLAINER_CONFIG.get('highlight_class', 'risk-high')

    # Build a single regex that matches any keyword using word boundaries.
    unique_keywords = sorted({k for k in keywords if k}, key=len, reverse=True)
    if not unique_keywords:
        return out

    # Escape keywords for regex and join with alternation
    pattern = r"\b(" + r"|".join(re.escape(k) for k in unique_keywords) + r")\b"
    regex = re.compile(pattern, flags=re.IGNORECASE)

    def _repl(m: re.Match) -> str:
        matched = m.group(0)
        return f"<{tag} class=\"{css_class}\">{matched}</{tag}>"

    return regex.sub(_repl, out)


def risk_factors_from_prediction(pred: Dict) -> List[str]:
    """Extract risk factors from prediction dictionary for explanation.

    Uses thresholds and templates from `EXPLAINER_CONFIG`.
    """
    templates = EXPLAINER_CONFIG.get('templates', {})
    urgency_threshold = EXPLAINER_CONFIG.get('urgency_threshold', 6)

    factors = []
    if pred.get('keywords'):
        keywords = ', '.join(pred['keywords'])
        tpl = templates.get('keywords', 'High-risk keywords: {keywords}')
        factors.append(tpl.format(keywords=keywords))

    urgency = float(pred.get('urgency_score', 0))
    if urgency >= urgency_threshold:
        tpl = templates.get('urgency', 'Urgency detected (score {score}/10)')
        factors.append(tpl.format(score=int(urgency)))

    if pred.get('model_probs'):
        # Produce a compact model agreement string from available probs
        probs = pred.get('model_probs', {})
        details = ', '.join(f"{k}={v:.2f}" for k, v in probs.items())
        tpl = templates.get('model_agreement', 'Model agreement: {details}')
        factors.append(tpl.format(details=details))

    return factors
