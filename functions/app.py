"""
Netlify serverless function wrapper for Flask application
"""
import sys
import os

# Add the parent directory to the path to import the app module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import app

# Netlify Functions handler
def handler(event, context):
    """
    AWS Lambda/Netlify Functions handler
    """
    # Import the serverless WSGI adapter
    try:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    except ImportError:
        pass
    
    # For Netlify Functions, we need to use serverless-wsgi
    try:
        import serverless_wsgi
        return serverless_wsgi.handle_request(app, event, context)
    except ImportError:
        # Fallback: return error response
        return {
            'statusCode': 500,
            'body': 'serverless-wsgi not installed. Please add it to requirements.txt'
        }
