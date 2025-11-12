"""Analytics module for dashboard and reporting."""
from .database import (
    init_db, 
    log_prediction, 
    get_analytics_data, 
    update_daily_statistics, 
    update_phishing_patterns,
    get_user_awareness_stats, 
    get_attack_heatmap
)

__all__ = [
    'init_db',
    'log_prediction',
    'get_analytics_data',
    'update_daily_statistics',
    'update_phishing_patterns',
    'get_user_awareness_stats',
    'get_attack_heatmap'
]
