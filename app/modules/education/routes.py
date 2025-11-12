"""
Education Routes Blueprint
Handles security awareness and education content delivery.
"""
from flask import Blueprint, jsonify

from app.modules.education import (
    get_user_education_tips,
    get_account_security_tips,
    get_patch_management_tips
)
from app.config import FEATURES

# Create blueprint
education_bp = Blueprint('education', __name__, url_prefix='/api')


@education_bp.route('/security-tips')
def api_security_tips():
    """Get security education tips and best practices."""
    if not FEATURES['education_module_enabled']:
        return jsonify({'error': 'Education module is disabled'}), 403
        
    return jsonify({
        'user_education': get_user_education_tips(),
        'account_security': get_account_security_tips(),
        'patch_management': get_patch_management_tips()
    })
