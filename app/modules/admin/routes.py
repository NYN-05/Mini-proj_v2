"""
Admin Routes Blueprint
Handles administrative dashboard interface.
"""
from flask import Blueprint, render_template

from app.config import FEATURES

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    """Render admin analytics dashboard."""
    if not FEATURES['admin_dashboard_enabled']:
        return "Admin dashboard is disabled", 403
        
    return render_template('admin_dashboard.html')
