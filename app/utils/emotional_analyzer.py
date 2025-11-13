"""
Emotional Tone & Sentiment Analysis for Social Engineering Detection

This module analyzes text for emotional manipulation tactics commonly used
in phishing and social engineering attacks. It detects abnormal emotional
markers such as urgency, fear, greed, anxiety, and excessive deference that
signal potential malicious intent.
"""
import re
from typing import Dict, List, Tuple, Any
from collections import defaultdict


# Emotional marker patterns with intensity weights
EMOTIONAL_PATTERNS = {
    'urgency': {
        'patterns': [
            (r'\b(urgent|immediately|asap|right\s+now|act\s+now|hurry)\b', 8),
            (r'\b(time\s+sensitive|deadline|expires?|expiring|limited\s+time)\b', 7),
            (r'\b(today|tonight|within\s+\d+\s+(hours?|minutes?))\b', 6),
            (r'\b(quick(ly)?|fast|instant(ly)?|prompt(ly)?)\b', 5),
            (r'\b(don\'?t\s+wait|can\'?t\s+wait|won\'?t\s+last)\b', 7),
            (r'\b(final\s+(notice|warning|chance|reminder))\b', 9),
        ],
        'weight': 1.2  # Urgency is a strong phishing indicator
    },
    'fear': {
        'patterns': [
            (r'\b(suspend(ed)?|deactivat(e|ed)|locked|blocked|disabled)\b', 9),
            (r'\b(unauthorized|unusual|suspicious|illegal)\s+(activity|access|login|transaction)\b', 8),
            (r'\b(security\s+(alert|breach|issue|warning|threat))\b', 8),
            (r'\b(compromise(d)?|hack(ed)?|vulnerab(le|ility))\b', 9),
            (r'\b(lose|lost|forfeit|cancel(led)?)\s+(access|account|eligibility|funds?)\b', 8),
            (r'\b(consequence|penalty|fine|legal\s+action|law\s+enforcement)\b', 7),
            (r'\b(danger|risk|threat|warning)\b', 6),
        ],
        'weight': 1.3  # Fear tactics are very common in phishing
    },
    'greed': {
        'patterns': [
            (r'\b(won|winner|winning|prize|reward|bonus)\b', 7),
            (r'\b(free|complimentary|no\s+cost|zero\s+cost)\b', 5),
            (r'\b(discount|save|savings|deal|offer)\b', 4),
            (r'\b(cash|money|\$\d+|refund|reimbursement)\b', 6),
            (r'\b(grant|scholarship|award|approved)\b', 6),
            (r'\b(claim|redeem|collect)\s+(your|now)\b', 7),
            (r'\b(limited\s+offer|exclusive|special\s+offer)\b', 5),
            (r'\b(congratulations?|you\'?ve\s+been\s+selected)\b', 8),
        ],
        'weight': 1.1  # Greed-based lures are common
    },
    'anxiety': {
        'patterns': [
            (r'\b(verify|confirm|validate|authenticate)\s+(your|account|identity|credentials)\b', 8),
            (r'\b(update|provide|enter|submit)\s+(your|password|details|information)\b', 7),
            (r'\b(action\s+required|immediate\s+action|must\s+act)\b', 8),
            (r'\b(error|problem|issue|failure)\b', 6),
            (r'\b(unable\s+to|failed\s+to|could\s+not)\b', 5),
            (r'\b(attention\s+required|requires?\s+your\s+attention)\b', 7),
            (r'\b(review|check)\s+(your|the)\b', 4),
        ],
        'weight': 1.15  # Anxiety inducing language is a red flag
    },
    'deference': {
        'patterns': [
            (r'\b(dear\s+(valued|esteemed|honored|distinguished))\b', 6),
            (r'\b(official|authorized|legitimate|verified)\b', 5),
            (r'\b(department|office|division|bureau|administration)\b', 4),
            (r'\b(notice|notification|alert)\s+from\b', 5),
            (r'\b(on\s+behalf\s+of|representing)\b', 4),
            (r'\b(compliance|regulation|policy|mandate)\b', 5),
        ],
        'weight': 0.9  # Deference is less strong but still relevant
    },
    'manipulation': {
        'patterns': [
            (r'\b(click\s+(here|below|link|now))\b', 7),
            (r'\b(do\s+not|don\'?t)\s+(ignore|delay|miss|disregard)\b', 7),
            (r'\b(only\s+you|you\'?ve\s+been\s+chosen)\b', 6),
            (r'\b(confidential|secret|private|sensitive)\b', 5),
            (r'\b(trust(ed)?|secure|safe|protected)\b', 4),
            (r'\b(guarantee(d)?|certain|sure|promise)\b', 5),
        ],
        'weight': 1.1
    }
}

# Sentiment word lists
POSITIVE_WORDS = {
    'congratulations', 'approved', 'success', 'winner', 'selected', 'eligible',
    'great', 'excellent', 'wonderful', 'fantastic', 'amazing', 'perfect',
    'benefit', 'opportunity', 'advantage', 'gain', 'profit', 'reward'
}

NEGATIVE_WORDS = {
    'suspend', 'cancel', 'terminate', 'denied', 'rejected', 'failed', 'error',
    'problem', 'issue', 'warning', 'alert', 'danger', 'risk', 'threat',
    'unauthorized', 'illegal', 'fraud', 'scam', 'suspicious', 'unusual'
}


def _get_empty_analysis() -> Dict[str, Any]:
    """Return empty/safe analysis structure when input is invalid."""
    return {
        'emotional_scores': {
            emotion: {'score': 0, 'count': 0, 'raw_score': 0, 'detected': []}
            for emotion in ['urgency', 'fear', 'greed', 'anxiety', 'deference', 'manipulation']
        },
        'hidden_meaning_score': 0,
        'sentiment': {'polarity': 0, 'label': 'neutral', 'positive_count': 0, 'negative_count': 0},
        'emotional_conflict': {'has_conflict': False, 'description': 'No emotional markers detected'},
        'manipulation_risk': {'level': 'LOW', 'score': 0, 'description': 'No manipulation detected'},
        'total_emotional_markers': 0,
        'composite_intensity': 0,
        'risk_factors': []
    }


def analyze_emotional_tone(text: str) -> Dict[str, Any]:
    """
    Analyze email text for emotional manipulation tactics.
    
    Returns comprehensive emotional analysis including:
    - Individual emotional marker scores
    - Overall hidden meaning score
    - Detected patterns and their intensities
    - Sentiment polarity
    """
    # Input validation and sanitization
    if not text or not isinstance(text, str):
        return _get_empty_analysis()
    
    # Limit text length for performance (already validated in routes, but double-check)
    if len(text) > 100000:
        text = text[:100000]
    
    try:
        text_lower = text.lower()
    except Exception:
        return _get_empty_analysis()
    
    # Detect emotional markers
    emotional_scores = {}
    detected_markers = defaultdict(list)
    total_intensity = 0
    total_matches = 0
    
    try:
        for emotion, config in EMOTIONAL_PATTERNS.items():
            score = 0
            count = 0
            matches = []
            
            try:
                for pattern, intensity in config['patterns']:
                    try:
                        found = re.findall(pattern, text_lower, re.IGNORECASE)
                        if found:
                            match_count = len(found)
                            weighted_score = intensity * match_count * config['weight']
                            score += weighted_score
                            count += match_count
                            total_matches += match_count
                            total_intensity += weighted_score
                            
                            # Store detected patterns (first few examples)
                            for match in found[:3]:
                                if isinstance(match, tuple):
                                    match_text = ' '.join(str(m) for m in match if m)
                                else:
                                    match_text = str(match)
                                matches.append({
                                    'text': match_text,
                                    'intensity': intensity,
                                    'pattern_type': emotion
                                })
                    except Exception:
                        # Skip this pattern if regex fails
                        continue
            except Exception:
                # Skip this emotion category if processing fails
                continue
            
            # Normalize to 0-10 scale
            normalized_score = min(score / 10, 10) if score > 0 else 0
            
            emotional_scores[emotion] = {
                'score': round(normalized_score, 2),
                'count': count,
                'raw_score': round(score, 2),
                'detected': matches[:5]  # Top 5 examples
            }
            
            detected_markers[emotion] = matches
    except Exception:
        # If complete failure, return empty analysis
        return _get_empty_analysis()
    
    # Calculate sentiment polarity
    try:
        sentiment = calculate_sentiment(text_lower)
    except Exception:
        sentiment = {'polarity': 0, 'label': 'neutral', 'positive_count': 0, 'negative_count': 0, 'mixed_sentiment': False, 'sentiment_words': 0}
    
    # Calculate hidden meaning score (composite)
    try:
        hidden_meaning_score = calculate_hidden_meaning_score(
            emotional_scores, sentiment, text_lower
        )
    except Exception:
        hidden_meaning_score = 0
    
    # Detect emotional conflict (mixed signals)
    try:
        emotional_conflict = detect_emotional_conflict(emotional_scores, sentiment)
    except Exception:
        emotional_conflict = {'has_conflict': False, 'description': 'Unable to analyze conflict'}
    
    # Calculate manipulation likelihood
    try:
        manipulation_risk = calculate_manipulation_risk(emotional_scores, sentiment)
    except Exception:
        manipulation_risk = {'level': 'UNKNOWN', 'score': 0, 'description': 'Unable to calculate risk'}
    
    # Generate risk factors
    try:
        risk_factors = generate_risk_factors(emotional_scores, sentiment)
    except Exception:
        risk_factors = []
    
    return {
        'emotional_scores': emotional_scores,
        'hidden_meaning_score': hidden_meaning_score,
        'sentiment': sentiment,
        'emotional_conflict': emotional_conflict,
        'manipulation_risk': manipulation_risk,
        'total_emotional_markers': total_matches,
        'composite_intensity': round(total_intensity / max(total_matches, 1), 2) if total_matches > 0 else 0,
        'risk_factors': risk_factors
    }


def calculate_sentiment(text: str) -> Dict[str, Any]:
    """Calculate basic sentiment polarity."""
    words = re.findall(r'\b\w+\b', text.lower())
    
    positive_count = sum(1 for w in words if w in POSITIVE_WORDS)
    negative_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    total_sentiment_words = positive_count + negative_count
    
    if total_sentiment_words == 0:
        polarity = 0
        label = 'neutral'
    else:
        # Polarity: -1 (very negative) to +1 (very positive)
        polarity = (positive_count - negative_count) / total_sentiment_words
        
        if polarity > 0.3:
            label = 'positive'
        elif polarity < -0.3:
            label = 'negative'
        else:
            label = 'neutral'
    
    # Detect mixed sentiment (common in phishing)
    mixed = positive_count > 0 and negative_count > 0
    
    return {
        'polarity': round(polarity, 3),
        'label': label,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'mixed_sentiment': mixed,
        'sentiment_words': total_sentiment_words
    }


def calculate_hidden_meaning_score(
    emotional_scores: Dict, 
    sentiment: Dict, 
    text: str
) -> float:
    """
    Calculate hidden meaning score (0-100) based on emotional manipulation patterns.
    
    Higher scores indicate more likely social engineering attempt.
    """
    # Base score from emotional markers
    emotion_sum = sum(e['score'] for e in emotional_scores.values())
    emotion_avg = emotion_sum / len(emotional_scores) if emotional_scores else 0
    
    # Weight critical emotions more heavily
    critical_emotions = ['urgency', 'fear', 'anxiety']
    critical_score = sum(
        emotional_scores[e]['score'] * 1.5 
        for e in critical_emotions 
        if e in emotional_scores
    ) / len(critical_emotions)
    
    # Penalize mixed sentiment (manipulation tactic)
    sentiment_penalty = 15 if sentiment['mixed_sentiment'] else 0
    
    # Penalize excessive positive with negative elements
    if sentiment['label'] == 'positive' and sentiment['negative_count'] > 2:
        sentiment_penalty += 10
    
    # Check for classic phishing combination: urgency + fear + action required
    combo_bonus = 0
    if (emotional_scores['urgency']['score'] > 5 and 
        emotional_scores['fear']['score'] > 5 and
        emotional_scores['anxiety']['score'] > 5):
        combo_bonus = 20
    
    # Calculate base score
    base_score = (emotion_avg * 3 + critical_score * 4) / 7
    
    # Add penalties and bonuses
    final_score = min(base_score * 10 + sentiment_penalty + combo_bonus, 100)
    
    return round(final_score, 2)


def detect_emotional_conflict(emotional_scores: Dict, sentiment: Dict) -> Dict[str, Any]:
    """Detect conflicting emotional signals (common in manipulation)."""
    conflicts = []
    
    # Positive sentiment with fear/urgency
    if sentiment['label'] == 'positive':
        if emotional_scores['fear']['score'] > 4:
            conflicts.append('positive_with_fear')
        if emotional_scores['urgency']['score'] > 6:
            conflicts.append('positive_with_urgency')
    
    # High greed with high fear (too good to be true + consequences)
    if (emotional_scores['greed']['score'] > 5 and 
        emotional_scores['fear']['score'] > 5):
        conflicts.append('greed_fear_conflict')
    
    # Deference with urgency (formal + rushed)
    if (emotional_scores['deference']['score'] > 4 and 
        emotional_scores['urgency']['score'] > 6):
        conflicts.append('deference_urgency_conflict')
    
    has_conflict = len(conflicts) > 0
    conflict_score = len(conflicts) * 15  # Each conflict adds to suspicion
    
    return {
        'has_conflict': has_conflict,
        'conflicts': conflicts,
        'conflict_score': min(conflict_score, 50),
        'description': _describe_conflicts(conflicts)
    }


def calculate_manipulation_risk(emotional_scores: Dict, sentiment: Dict) -> Dict[str, Any]:
    """Calculate overall manipulation risk assessment."""
    # Count high-intensity emotions
    high_emotions = sum(1 for e in emotional_scores.values() if e['score'] > 6)
    
    # Check for manipulation pattern
    manipulation_score = emotional_scores.get('manipulation', {}).get('score', 0)
    
    # Risk factors
    risk_level = 'low'
    risk_score = 0
    
    if high_emotions >= 3 or manipulation_score > 7:
        risk_level = 'critical'
        risk_score = 90
    elif high_emotions >= 2 or manipulation_score > 5:
        risk_level = 'high'
        risk_score = 70
    elif high_emotions >= 1 or manipulation_score > 3:
        risk_level = 'medium'
        risk_score = 50
    else:
        risk_level = 'low'
        risk_score = 20
    
    return {
        'level': risk_level,
        'score': risk_score,
        'high_intensity_emotions': high_emotions,
        'manipulation_detected': manipulation_score > 4
    }


def generate_risk_factors(emotional_scores: Dict, sentiment: Dict) -> List[str]:
    """Generate human-readable risk factors from emotional analysis."""
    factors = []
    
    for emotion, data in emotional_scores.items():
        if data['score'] > 6:
            factors.append(
                f"High {emotion} indicators detected (score: {data['score']}/10, {data['count']} instances)"
            )
        elif data['score'] > 4:
            factors.append(
                f"Moderate {emotion} patterns found (score: {data['score']}/10)"
            )
    
    if sentiment['mixed_sentiment']:
        factors.append(
            f"Mixed emotional tone detected ({sentiment['positive_count']} positive, "
            f"{sentiment['negative_count']} negative indicators)"
        )
    
    if sentiment['label'] == 'positive' and sentiment['negative_count'] > 2:
        factors.append(
            "Suspicious positive framing with underlying negative elements"
        )
    
    return factors


def _describe_conflicts(conflicts: List[str]) -> str:
    """Generate human-readable conflict descriptions."""
    descriptions = {
        'positive_with_fear': 'Positive messaging with fear tactics',
        'positive_with_urgency': 'Positive framing with urgent pressure',
        'greed_fear_conflict': 'Reward promises combined with threats',
        'deference_urgency_conflict': 'Formal tone with inappropriate urgency'
    }
    return ', '.join(descriptions.get(c, c) for c in conflicts)


def get_emotional_summary(analysis: Dict) -> str:
    """Generate a brief summary of emotional analysis for display."""
    score = analysis['hidden_meaning_score']
    risk = analysis['manipulation_risk']['level']
    
    if score > 70:
        return f"⚠️ CRITICAL: Strong emotional manipulation detected (score: {score}/100, risk: {risk})"
    elif score > 50:
        return f"⚠️ HIGH: Significant emotional manipulation indicators (score: {score}/100, risk: {risk})"
    elif score > 30:
        return f"⚠ MODERATE: Some emotional manipulation patterns detected (score: {score}/100, risk: {risk})"
    else:
        return f"✓ LOW: Minimal emotional manipulation detected (score: {score}/100, risk: {risk})"
