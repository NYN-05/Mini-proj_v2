"""
EduShield Configuration Module
Centralizes all configuration settings, paths, and constants.
"""

from pathlib import Path

# ========== Project Paths ==========
PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

# ========== Database Configuration ==========
DB_PATH = DATA_DIR / "edushield_analytics.db"
DEFAULT_INSTITUTION = "Default"

# ========== Model Configuration ==========
MODEL_FILES = {
    'vectorizer': MODELS_DIR / 'tfidf.pkl',
    'logistic': MODELS_DIR / 'logistic.pkl',
    'naive_bayes': MODELS_DIR / 'nb.pkl',
    'svm': MODELS_DIR / 'svm.pkl',
    # New: single pipeline that contains TF-IDF + stacking classifier
    'pipeline': MODELS_DIR / 'pipeline.pkl'
}

# TF-IDF Parameters
TFIDF_CONFIG = {
    'max_features': 5000,
    'ngram_range': (1, 3),
    'max_df': 0.95,
    'stop_words': 'english'
}

# Model Weights for Ensemble
MODEL_WEIGHTS = {
    'logistic': 0.4,
    'naive_bayes': 0.3,
    'svm': 0.3
}

# ========== Detection Configuration ==========
# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    'high': 0.85,
    'medium': 0.60,
    'low': 0.40
}

# Risk scoring weights for comprehensive detection
DETECTION_WEIGHTS = {
    'ai_ml': 0.60,          # AI/ML model prediction weight
    'url_filtering': 0.25,  # URL analysis weight
    'email_scanning': 0.25, # Email header/attachment scanning
    'behavior': 0.10,       # Behavioral analysis weight
    'threat_intel': 0.30    # Threat intelligence weight
}

# URL filtering configuration
SUSPICIOUS_TLDS = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work']
URL_SHORTENERS = ['bit.ly', 't.co', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly']
DANGEROUS_EXTENSIONS = ['.exe', '.scr', '.bat', '.cmd', '.vbs', '.js', '.jar', '.docm', '.xlsm', '.pptm']

# ========== Flask Configuration ==========
FLASK_CONFIG = {
    'TEMPLATE_FOLDER': 'templates',
    'STATIC_FOLDER': 'static',
    'DEBUG': False,
    'HOST': '0.0.0.0',
    'PORT': 5000
}

# ========== Analytics Configuration ==========
# Default time ranges for analytics queries
ANALYTICS_DEFAULTS = {
    'days': 30,
    'heatmap_days': 7,
    'trends_days': 90
}

# Chart color schemes
CHART_COLORS = {
    'primary': '#0f62fe',
    'success': '#24a148',
    'danger': '#da1e28',
    'warning': '#f1c21b',
    'info': '#1192e8',
    'secondary': '#6f6f6f'
}

# ========== Security Education Configuration ==========
MAX_TIPS_PER_REQUEST = 10

# ========== Logging Configuration ==========
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'

# ========== Feature Flags ==========
FEATURES = {
    'analytics_enabled': True,
    'admin_dashboard_enabled': True,
    'advanced_detection_enabled': False,  # Disabled - comprehensive detection removed during cleanup
    'education_module_enabled': True,
    'behavior_analysis_enabled': False,  # Part of advanced detection
    'threat_intelligence_enabled': False  # Part of advanced detection
}


# ========== Explainer / Explainability Configuration ==========
# Centralize text/HTML templates and thresholds used by explainability helpers.
EXPLAINER_CONFIG = {
    # CSS class to wrap high-risk keywords with
    'highlight_class': 'risk-high',
    # HTML tag used for highlighting (span, mark, etc.)
    'highlight_tag': 'span',
    # Whether to escape HTML in input text before highlighting
    'escape_html': True,
    # Urgency score threshold (0-10 scale) above which urgency is reported
    'urgency_threshold': 6,
    # Label templates (formatted with .format or f-strings)
    'templates': {
        'keywords': 'High-risk keywords: {keywords}',
        'urgency': 'Urgency detected (score {score}/10)',
        'model_agreement': 'Model agreement: {details}'
    }
}
