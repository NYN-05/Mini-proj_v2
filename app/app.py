"""
EduShield - Academic Email Phishing Detection System
Main Flask application with modular architecture.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from flask import Flask

# Import configuration
from app.config import FLASK_CONFIG, FEATURES

# Import blueprints
from app.core.routes import core_bp
from app.modules.analytics.routes import analytics_bp
from app.modules.admin.routes import admin_bp
from app.modules.education.routes import education_bp

# Import database initialization
from app.modules.analytics import init_db


def create_app():
    """Application factory pattern for creating Flask app."""
    app = Flask(
        __name__,
        template_folder=FLASK_CONFIG['TEMPLATE_FOLDER'],
        static_folder=FLASK_CONFIG['STATIC_FOLDER']
    )
    
    # Initialize database if analytics enabled
    if FEATURES['analytics_enabled']:
        init_db()
        print('[App] Analytics database initialized.')
    
    # Register blueprints
    app.register_blueprint(core_bp)
    
    if FEATURES['analytics_enabled']:
        app.register_blueprint(analytics_bp)
        print('[App] Analytics routes registered.')
    
    if FEATURES['admin_dashboard_enabled']:
        app.register_blueprint(admin_bp)
        print('[App] Admin dashboard routes registered.')
    
    if FEATURES['education_module_enabled']:
        app.register_blueprint(education_bp)
        print('[App] Education routes registered.')
    
    print('[App] EduShield application initialized successfully.')
    print(f'[App] Features enabled: {[k for k, v in FEATURES.items() if v]}')
    
    return app


# Create application instance
app = create_app()


if __name__ == '__main__':
    app.run(
        debug=FLASK_CONFIG['DEBUG'],
        host=FLASK_CONFIG['HOST'],
        port=FLASK_CONFIG['PORT']
    )
