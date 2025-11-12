"""
Core Detection Routes Blueprint
Handles the main phishing detection functionality.
"""
from flask import Blueprint, render_template, request, jsonify
from pathlib import Path

from app.core import (
    ModelBundle, predict_phishing, highlight_keywords, risk_factors_from_prediction,
    filter_urls, get_url_risk_summary
)
from app.modules.analytics import log_prediction, update_daily_statistics, update_phishing_patterns
from app.config import PROJECT_ROOT, DEFAULT_INSTITUTION, FEATURES

# Create blueprint
core_bp = Blueprint('core', __name__)

# Load models on startup
MODEL_BUNDLE = None
try:
    MODEL_BUNDLE = ModelBundle(PROJECT_ROOT)
    print('[Core] ML models loaded successfully.')
except Exception as e:
    print(f'[Core] Models not loaded: {e}')


@core_bp.route('/')
def index():
    """Render main phishing detection interface."""
    return render_template('index.html')


@core_bp.route('/detect', methods=['POST'])
def detect_phishing():
    """Detect phishing using basic AI/ML models."""
    data = request.get_json() or {}
    email_text = data.get('email_text', '')
    institution = data.get('institution', DEFAULT_INSTITUTION)
    user_id = data.get('user_id', 'anonymous')
    
    if not email_text:
        return jsonify({'error': 'No email_text provided'}), 400

    if MODEL_BUNDLE is None:
        return jsonify({'error': 'Models not found. Run training script first (src/train_models.py)'}), 500

    # 1. Basic AI/ML prediction
    pred = predict_phishing(email_text, MODEL_BUNDLE)
    
    # 2. URL filtering analysis
    url_analysis = filter_urls(email_text)
    url_risk_factors = get_url_risk_summary(url_analysis)
    
    # 3. Combine ML score with URL risk
    # If URLs are highly suspicious, increase phishing confidence
    url_risk_weight = 0.3  # URL analysis contributes 30% to final score
    ml_weight = 0.7  # ML models contribute 70% to final score
    
    url_risk_normalized = url_analysis['overall_risk'] / 100
    combined_confidence = (ml_weight * pred['confidence']) + (url_risk_weight * url_risk_normalized)
    
    # Adjust classification based on combined score
    if url_analysis['has_suspicious_urls'] and url_analysis['overall_risk'] >= 50:
        # High-risk URLs detected - increase likelihood of phishing
        combined_confidence = max(combined_confidence, 0.7)
        final_classification = 'PHISHING'
    elif combined_confidence >= 0.5:
        final_classification = 'PHISHING'
    else:
        final_classification = 'LEGITIMATE'
    
    # Log prediction to analytics database
    if FEATURES['analytics_enabled']:
        try:
            log_prediction(
                classification=final_classification,
                confidence=combined_confidence,
                email_text=email_text,
                model_scores=pred['model_probs'],
                urgency_score=pred.get('urgency_score', 0),
                keywords=pred.get('keywords', []),
                institution=institution
            )
            update_daily_statistics(institution)
            update_phishing_patterns(
                classification=final_classification,
                confidence=combined_confidence,
                keywords=pred.get('keywords', []),
                institution=institution
            )
        except Exception as e:
            print(f'[Core] Analytics logging failed: {e}')
    
    # Prepare response with explanation
    highlighted_text = highlight_keywords(email_text, pred.get('keywords', []))
    risk_factors = risk_factors_from_prediction(pred)
    
    # Add URL-based risk factors
    risk_factors.extend(url_risk_factors)
    
    response = {
        'classification': final_classification,
        'confidence': float(combined_confidence),
        'ml_confidence': pred['confidence'],
        'model_probs': pred['model_probs'],
        'urgency_score': pred.get('urgency_score', 0),
        'keywords': pred.get('keywords', []),
        'highlighted_text': highlighted_text,
        'risk_factors': risk_factors,
        # URL analysis details
        'url_analysis': {
            'urls_found': url_analysis['urls_found'],
            'high_risk_urls': len(url_analysis['high_risk_urls']),
            'medium_risk_urls': len(url_analysis['medium_risk_urls']),
            'overall_url_risk': url_analysis['overall_risk'],
            'suspicious_urls': url_analysis['has_suspicious_urls'],
            'url_details': url_analysis['urls']
        }
    }
    
    return jsonify(response)


# Note: Advanced detection endpoint disabled - comprehensive_phishing_detection
# functionality was removed during cleanup. To re-enable, implement the 
# comprehensive detection logic or restore from app/utils/advanced_detection.py
#
# @core_bp.route('/detect/advanced', methods=['POST'])
# def detect_advanced():
#     """Detect phishing using comprehensive multi-technique analysis."""
#     return jsonify({'error': 'Advanced detection temporarily disabled'}), 501

