"""Explainability helpers: highlight keywords and produce risk factors."""
from typing import List, Dict
import html


def highlight_keywords(text: str, keywords: List[str]) -> str:
    """Return HTML where keywords are wrapped in span tags with classes."""
    if not keywords:
        return html.escape(text)

    escaped = html.escape(text)
    # naive replace: lower/upper issues handled by simple token replacement using words boundaries
    out = escaped
    for kw in sorted(set(keywords), key=len, reverse=True):
        out = out.replace(kw, f"<span class=\"risk-high\">{kw}</span>")
        out = out.replace(kw.capitalize(), f"<span class=\"risk-high\">{kw.capitalize()}</span>")
    return out


def risk_factors_from_prediction(pred: Dict) -> List[str]:
    """Extract risk factors from prediction dictionary for explanation."""
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
