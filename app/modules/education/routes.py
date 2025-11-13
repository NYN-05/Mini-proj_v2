from flask import Blueprint, jsonify

education_bp = Blueprint('education', __name__, url_prefix='/education')


@education_bp.route('/tips')
def tips():
    """Return a small set of security tips for educational UI."""
    tips_list = [
        'Do not click suspicious links',
        'Verify sender via official channels',
        'Do not provide credentials via email',
        'Report suspected phishing to IT'
    ]
    return jsonify({'tips': tips_list})
