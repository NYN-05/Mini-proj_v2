"""
Analytics Routes Blueprint
Handles admin dashboard and analytics API endpoints.
"""
from flask import Blueprint, request, jsonify

from app.modules.analytics import get_analytics_data, get_attack_heatmap, get_user_awareness_stats
from app.config import DEFAULT_INSTITUTION, ANALYTICS_DEFAULTS, FEATURES

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api')


@analytics_bp.route('/analytics')
def api_analytics():
    """Get comprehensive analytics data."""
    if not FEATURES['analytics_enabled']:
        return jsonify({'error': 'Analytics is disabled'}), 403
        
    institution = request.args.get('institution', DEFAULT_INSTITUTION)
    days = request.args.get('days', ANALYTICS_DEFAULTS['days'], type=int)
    
    try:
        analytics = get_analytics_data(institution, days)
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/heatmap')
def api_heatmap():
    """Get hourly attack heatmap data."""
    if not FEATURES['analytics_enabled']:
        return jsonify({'error': 'Analytics is disabled'}), 403
        
    institution = request.args.get('institution', DEFAULT_INSTITUTION)
    days = request.args.get('days', ANALYTICS_DEFAULTS['heatmap_days'], type=int)
    
    try:
        heatmap = get_attack_heatmap(institution, days)
        return jsonify(heatmap)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/user-awareness')
def api_user_awareness():
    """Get user awareness statistics."""
    if not FEATURES['analytics_enabled']:
        return jsonify({'error': 'Analytics is disabled'}), 403
        
    institution = request.args.get('institution', DEFAULT_INSTITUTION)
    
    try:
        stats = get_user_awareness_stats(institution)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
