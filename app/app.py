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
import logging
from collections import defaultdict
from datetime import datetime, timedelta
import html

# Import configuration
from app.config import FLASK_CONFIG, FEATURES, SECURITY_CONFIG, SECURITY_HEADERS

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
    
    # Security configuration
    app.config['SECRET_KEY'] = FLASK_CONFIG['SECRET_KEY']
    app.config['MAX_CONTENT_LENGTH'] = FLASK_CONFIG['MAX_CONTENT_LENGTH']
    app.config['JSON_SORT_KEYS'] = FLASK_CONFIG['JSON_SORT_KEYS']
    
    # Session security
    app.config['SESSION_COOKIE_SECURE'] = SECURITY_CONFIG.get('SESSION_COOKIE_SECURE', False)
    app.config['SESSION_COOKIE_HTTPONLY'] = SECURITY_CONFIG['SESSION_COOKIE_HTTPONLY']
    app.config['SESSION_COOKIE_SAMESITE'] = SECURITY_CONFIG['SESSION_COOKIE_SAMESITE']
    
    # Rate limiting (simple in-memory implementation)
    rate_limit_store = defaultdict(list)
    
    @app.before_request
    def rate_limit():
        """Simple rate limiting middleware."""
        from flask import request, jsonify
        
        # Only rate-limit API endpoints
        if request.path.startswith('/detect'):
            ip = request.remote_addr or 'unknown'
            now = datetime.now()
            
            # Clean old entries (older than 1 minute)
            rate_limit_store[ip] = [
                timestamp for timestamp in rate_limit_store[ip]
                if now - timestamp < timedelta(minutes=1)
            ]
            
            # Check rate limit
            if len(rate_limit_store[ip]) >= SECURITY_CONFIG['RATE_LIMIT_PER_MINUTE']:
                return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
            
            # Add current request
            rate_limit_store[ip].append(now)
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
