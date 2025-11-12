"""Database models and initialization for EduShield analytics."""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "edushield_analytics.db"


def init_db():
    """Initialize database with all required tables."""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table 1: Prediction History
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            email_text TEXT NOT NULL,
            classification TEXT NOT NULL,
            confidence REAL NOT NULL,
            urgency_score REAL,
            model_lr_score REAL,
            model_nb_score REAL,
            model_svm_score REAL,
            keywords TEXT,
            institution TEXT DEFAULT 'Default'
        )
    """)
    
    # Table 2: Daily Statistics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE UNIQUE,
            total_emails INTEGER DEFAULT 0,
            phishing_count INTEGER DEFAULT 0,
            legitimate_count INTEGER DEFAULT 0,
            avg_confidence REAL DEFAULT 0,
            high_confidence_phishing INTEGER DEFAULT 0,
            institution TEXT DEFAULT 'Default'
        )
    """)
    
    # Table 3: Phishing Patterns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phishing_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            keyword TEXT,
            frequency INTEGER DEFAULT 1,
            avg_confidence REAL DEFAULT 0,
            last_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
            institution TEXT DEFAULT 'Default'
        )
    """)
    
    # Table 4: User Awareness
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_awareness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            total_analyses INTEGER DEFAULT 0,
            phishing_detected INTEGER DEFAULT 0,
            legitimate_count INTEGER DEFAULT 0,
            highest_confidence REAL DEFAULT 0,
            last_analysis DATETIME DEFAULT CURRENT_TIMESTAMP,
            institution TEXT DEFAULT 'Default'
        )
    """)
    
    # Table 5: Model Performance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            accuracy REAL,
            precision REAL,
            recall REAL,
            f1_score REAL,
            auc_score REAL,
            total_predictions INTEGER,
            true_positives INTEGER,
            true_negatives INTEGER,
            false_positives INTEGER,
            false_negatives INTEGER,
            institution TEXT DEFAULT 'Default'
        )
    """)
    
    # Table 6: Attack Trends
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attack_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            hour INTEGER,
            attack_type TEXT,
            frequency INTEGER DEFAULT 1,
            avg_confidence REAL DEFAULT 0,
            institution TEXT DEFAULT 'Default'
        )
    """)
    
    conn.commit()
    conn.close()


def log_prediction(classification, confidence, email_text, model_scores, urgency_score=0, keywords=None, institution='Default'):
    """Log a prediction to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    keywords_str = ','.join(keywords) if keywords else ''
    
    cursor.execute("""
        INSERT INTO prediction_history 
        (email_text, classification, confidence, urgency_score, model_lr_score, model_nb_score, model_svm_score, keywords, institution)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        email_text[:500],  # Truncate for storage
        classification,
        confidence,
        urgency_score,
        model_scores.get('logistic', 0),
        model_scores.get('nb', 0),
        model_scores.get('svm', 0),
        keywords_str,
        institution
    ))
    
    conn.commit()
    conn.close()


def update_daily_statistics(institution='Default'):
    """Update daily statistics based on today's predictions."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    today = datetime.now().date()
    
    # Get stats for today
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN classification='PHISHING' THEN 1 ELSE 0 END) as phishing_count,
            SUM(CASE WHEN classification='LEGITIMATE' THEN 1 ELSE 0 END) as legitimate_count,
            AVG(confidence) as avg_conf,
            SUM(CASE WHEN classification='PHISHING' AND confidence > 0.8 THEN 1 ELSE 0 END) as high_conf
        FROM prediction_history
        WHERE DATE(timestamp) = ? AND institution = ?
    """, (today, institution))
    
    result = cursor.fetchone()
    
    if result and result[0] > 0:
        total, phishing_count, legitimate_count, avg_conf, high_conf = result
        
        cursor.execute("""
            INSERT OR REPLACE INTO daily_statistics 
            (date, total_emails, phishing_count, legitimate_count, avg_confidence, high_confidence_phishing, institution)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (today, total, phishing_count or 0, legitimate_count or 0, avg_conf or 0, high_conf or 0, institution))
        
        conn.commit()
    
    conn.close()


def get_analytics_data(institution='Default', days=30):
    """Retrieve comprehensive analytics data."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    analytics = {}
    
    # 1. Overall Statistics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_predictions,
            SUM(CASE WHEN classification='PHISHING' THEN 1 ELSE 0 END) as total_phishing,
            SUM(CASE WHEN classification='LEGITIMATE' THEN 1 ELSE 0 END) as total_legitimate,
            AVG(confidence) as avg_confidence,
            MAX(confidence) as max_confidence,
            MIN(confidence) as min_confidence
        FROM prediction_history
        WHERE institution = ?
    """, (institution,))
    row = cursor.fetchone()
    analytics['overall'] = dict(row)
    
    # 2. Daily Trends (last 30 days)
    cursor.execute("""
        SELECT date, total_emails, phishing_count, legitimate_count, avg_confidence
        FROM daily_statistics
        WHERE institution = ?
        ORDER BY date DESC
        LIMIT ?
    """, (institution, days))
    analytics['daily_trends'] = [dict(row) for row in cursor.fetchall()]
    
    # 3. Top Phishing Patterns
    cursor.execute("""
        SELECT pattern_type, keyword, frequency, avg_confidence
        FROM phishing_patterns
        WHERE institution = ?
        ORDER BY frequency DESC
        LIMIT 10
    """, (institution,))
    analytics['patterns'] = [dict(row) for row in cursor.fetchall()]
    
    # 4. Top Keywords
    # Keywords are stored as comma-separated strings in the `keywords` column.
    # Compute top keywords and average model_lr_score in Python to avoid complex
    # and error-prone SQL text manipulation.
    cursor.execute("""
        SELECT keywords, model_lr_score
        FROM prediction_history
        WHERE classification='PHISHING' AND institution = ? AND keywords IS NOT NULL
    """, (institution,))

    keyword_counts = {}
    keyword_risk_sum = {}

    rows = cursor.fetchall()
    for row in rows:
        # row may be sqlite3.Row (mapping) or tuple; handle both
        try:
            keywords_field = row['keywords']
            lr_score = row['model_lr_score']
        except Exception:
            keywords_field, lr_score = row[0], row[1]

        if not keywords_field:
            continue

        for kw in keywords_field.split(','):
            k = kw.strip().lower()
            if not k:
                continue
            keyword_counts[k] = keyword_counts.get(k, 0) + 1
            keyword_risk_sum[k] = keyword_risk_sum.get(k, 0.0) + (float(lr_score) if lr_score is not None else 0.0)

    top_keywords = []
    for k, freq in sorted(keyword_counts.items(), key=lambda item: item[1], reverse=True)[:15]:
        avg_risk = keyword_risk_sum.get(k, 0.0) / freq if freq else 0.0
        top_keywords.append({'keyword': k, 'frequency': freq, 'avg_risk': avg_risk})

    analytics['top_keywords'] = top_keywords
    
    # 5. Model Performance (Latest)
    cursor.execute("""
        SELECT accuracy, precision, recall, f1_score, auc_score, timestamp
        FROM model_performance
        WHERE institution = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (institution,))
    row = cursor.fetchone()
    analytics['model_performance'] = dict(row) if row else {}
    
    # 6. Hourly Attack Patterns
    cursor.execute("""
        SELECT 
            CAST(STRFTIME('%H', timestamp) AS INTEGER) as hour,
            COUNT(*) as frequency,
            SUM(CASE WHEN classification='PHISHING' THEN 1 ELSE 0 END) as phishing_count
        FROM prediction_history
        WHERE classification='PHISHING' AND institution = ?
        GROUP BY hour
        ORDER BY hour
    """, (institution,))
    analytics['hourly_patterns'] = [dict(row) for row in cursor.fetchall()]
    
    # 7. Confidence Distribution
    cursor.execute("""
        SELECT 
            CASE 
                WHEN confidence >= 0.9 THEN '90-100%'
                WHEN confidence >= 0.8 THEN '80-90%'
                WHEN confidence >= 0.7 THEN '70-80%'
                WHEN confidence >= 0.6 THEN '60-70%'
                ELSE 'Below 60%'
            END as confidence_range,
            COUNT(*) as count
        FROM prediction_history
        WHERE classification='PHISHING' AND institution = ?
        GROUP BY confidence_range
    """, (institution,))
    analytics['confidence_distribution'] = [dict(row) for row in cursor.fetchall()]
    
    # 8. Recent Predictions
    cursor.execute("""
        SELECT timestamp, classification, confidence, keywords
        FROM prediction_history
        WHERE institution = ?
        ORDER BY timestamp DESC
        LIMIT 20
    """, (institution,))
    analytics['recent_predictions'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return analytics


def get_user_awareness_stats(institution='Default'):
    """Get user awareness and usage statistics."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_users,
            AVG(total_analyses) as avg_analyses_per_user,
            AVG(phishing_detected) as avg_phishing_detected,
            SUM(total_analyses) as total_system_uses,
            SUM(phishing_detected) as total_phishing_caught
        FROM user_awareness
        WHERE institution = ?
    """, (institution,))
    
    result = cursor.fetchone()
    conn.close()
    
    return dict(result) if result else {}


def update_phishing_patterns(classification, confidence, keywords, institution='Default'):
    """Update phishing pattern statistics."""
    if classification != 'PHISHING' or not keywords:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for keyword in keywords:
        # Determine pattern type
        pattern_type = categorize_pattern(keyword)
        
        cursor.execute("""
            SELECT id, frequency, avg_confidence FROM phishing_patterns
            WHERE keyword = ? AND pattern_type = ? AND institution = ?
        """, (keyword, pattern_type, institution))
        
        existing = cursor.fetchone()
        
        if existing:
            pattern_id, freq, avg_conf = existing
            new_avg = (avg_conf * freq + confidence) / (freq + 1)
            cursor.execute("""
                UPDATE phishing_patterns
                SET frequency = frequency + 1, avg_confidence = ?, last_detected = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_avg, pattern_id))
        else:
            cursor.execute("""
                INSERT INTO phishing_patterns (pattern_type, keyword, frequency, avg_confidence, institution)
                VALUES (?, ?, 1, ?, ?)
            """, (pattern_type, keyword, confidence, institution))
    
    conn.commit()
    conn.close()


def categorize_pattern(keyword):
    """Categorize keyword into attack pattern type."""
    keyword_lower = keyword.lower()
    
    if any(k in keyword_lower for k in ['verify', 'confirm', 'authenticate', 'validate']):
        return 'Credential Harvesting'
    elif any(k in keyword_lower for k in ['urgent', 'immediately', 'asap', 'today', 'now']):
        return 'Urgency/Time Pressure'
    elif any(k in keyword_lower for k in ['scholarship', 'fee', 'payment', 'refund', 'money']):
        return 'Financial Fraud'
    elif any(k in keyword_lower for k in ['scholarship', 'award', 'prize', 'congratulations']):
        return 'Reward/Prize Scam'
    elif any(k in keyword_lower for k in ['deadline', 'expires', 'limited']):
        return 'Deadline Pressure'
    else:
        return 'Other'


def get_attack_heatmap(institution='Default', days=7):
    """Get hourly attack heatmap data for the last N days."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            DATE(timestamp) as date,
            CAST(STRFTIME('%H', timestamp) AS INTEGER) as hour,
            COUNT(*) as count
        FROM prediction_history
        WHERE classification='PHISHING' 
            AND institution = ?
            AND DATE(timestamp) >= DATE('now', '-' || ? || ' days')
        GROUP BY date, hour
        ORDER BY date, hour
    """, (institution, days))
    
    heatmap_data = [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    conn.close()
    
    return heatmap_data
