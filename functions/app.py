"""
Netlify serverless function wrapper for Flask application
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the path to import the app module
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Set environment variable for model loading
os.environ['FLASK_ENV'] = 'production'

try:
    from app.app import app
    from werkzeug.middleware.proxy_fix import ProxyFix
    
    # Apply proxy fix for proper request handling behind Netlify
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Disable debug mode in production
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    logger.info("Flask app loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Flask app: {e}")
    raise

# Netlify Functions handler
def handler(event, context):
    """
    AWS Lambda/Netlify Functions handler
    
    Args:
        event: Lambda event object
        context: Lambda context object
    
    Returns:
        Response dict with statusCode and body
    """
    try:
        import serverless_wsgi
        logger.info(f"Processing request: {event.get('path', '/')}")
        return serverless_wsgi.handle_request(app, event, context)
    except ImportError as e:
        logger.error(f"serverless-wsgi not found: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': '{"error": "Server configuration error. Please contact support."}'
        }
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': '{"error": "Internal server error"}'
        }
