# 🚀 EduShield Quick Reference - New Architecture

## 📁 File Locations (Quick Lookup)

### Configuration
```python
from app.config import *
# PROJECT_ROOT, DB_PATH, MODEL_FILES, FEATURES, etc.
```

### Core Detection
```python
from app.core import ModelBundle, predict_phishing
from app.core import highlight_keywords, risk_factors_from_prediction
```

### Analytics
```python
from app.modules.analytics import (
    init_db, log_prediction, get_analytics_data,
    update_daily_statistics, update_phishing_patterns,
    get_user_awareness_stats, get_attack_heatmap
)
```

### Education
```python
from app.modules.education import (
    get_user_education_tips,
    get_account_security_tips,
    get_patch_management_tips
)
```

## 🎯 Common Tasks

### Task 1: Start the Application
```bash
# New modular app (recommended)
python app/app_new.py

# Legacy app (backward compatibility)
python app/app.py
```

### Task 2: Make a Prediction
```python
from app.core import ModelBundle, predict_phishing
from app.config import PROJECT_ROOT

bundle = ModelBundle(PROJECT_ROOT)
result = predict_phishing("Urgent! Verify your account now!", bundle)
print(result['classification'])  # PHISHING or LEGITIMATE
```

### Task 3: Log Prediction to Analytics
```python
from app.modules.analytics import log_prediction

log_prediction(
    classification='PHISHING',
    confidence=0.95,
    email_text='Test email',
    model_scores={'logistic': 0.9, 'nb': 0.85, 'svm': 0.92},
    institution='My University'
)
```

### Task 4: Get Analytics Data
```python
from app.modules.analytics import get_analytics_data

analytics = get_analytics_data(institution='My University', days=30)
print(analytics['overall'])  # Overall statistics
print(analytics['daily_trends'])  # Daily trends
```

### Task 5: Toggle Features
Edit `app/config.py`:
```python
FEATURES = {
    'analytics_enabled': True,  # Enable/disable analytics
    'admin_dashboard_enabled': True,
    'advanced_detection_enabled': True,
    'education_module_enabled': True,
}
```

## 🌐 API Endpoints

### Core Detection
- `GET /` - Main detection UI
- `POST /detect` - Basic ML detection
- `POST /detect/advanced` - Comprehensive detection

### Analytics API
- `GET /api/analytics?institution=X&days=30` - Analytics data
- `GET /api/heatmap?institution=X&days=7` - Attack heatmap
- `GET /api/user-awareness?institution=X` - User stats

### Admin
- `GET /admin` - Admin dashboard

### Education
- `GET /api/security-tips` - Security tips

## 🔧 Configuration Quick Reference

### Paths
```python
from app.config import PROJECT_ROOT, MODELS_DIR, DB_PATH
```

### ML Configuration
```python
from app.config import TFIDF_CONFIG, MODEL_WEIGHTS, MODEL_FILES
```

### Detection Settings
```python
from app.config import (
    CONFIDENCE_THRESHOLDS,
    DETECTION_WEIGHTS,
    SUSPICIOUS_TLDS,
    DANGEROUS_EXTENSIONS
)
```

### Feature Flags
```python
from app.config import FEATURES

if FEATURES['analytics_enabled']:
    # Do analytics stuff
```

## 📊 Module Purpose

| Module | Purpose | Usage Frequency |
|--------|---------|----------------|
| `core/` | ML detection | High (every request) |
| `modules/analytics/` | Data logging | Medium (background) |
| `modules/admin/` | Dashboard | Low (admin only) |
| `modules/education/` | Security tips | Low (informational) |

## 🛠️ Development Patterns

### Pattern 1: Adding a New Detection Feature
1. Add to `app/core/predictor.py` or create new file in `app/core/`
2. Update `app/core/routes.py` if new endpoint needed
3. Import in `app/core/__init__.py`

### Pattern 2: Adding New Analytics
1. Add database table in `app/modules/analytics/database.py`
2. Add API endpoint in `app/modules/analytics/routes.py`
3. Update admin dashboard to display

### Pattern 3: Adding Configuration
1. Add setting to `app/config.py`
2. Import where needed: `from app.config import SETTING_NAME`

## 🧪 Testing Quick Commands

```bash
# Run all tests
pytest tests/

# Test specific module
pytest tests/test_predictor.py

# Test with coverage
pytest --cov=app tests/

# Run app for manual testing
python app/app_new.py
```

## 📝 Import Cheat Sheet

### ❌ Old Imports (Don't Use)
```python
from app.utils.predictor import ModelBundle
from app.database import log_prediction
from app.utils.advanced_detection import get_user_education_tips
```

### ✅ New Imports (Use These)
```python
from app.core import ModelBundle
from app.modules.analytics import log_prediction
from app.modules.education import get_user_education_tips
```

## 🔍 Troubleshooting

### Issue: Import Error
```python
# Error: ImportError: cannot import name 'ModelBundle'
# Solution: Update import path
from app.core import ModelBundle  # NEW PATH
```

### Issue: 404 Not Found
```python
# Check feature flags in app/config.py
FEATURES = {
    'analytics_enabled': True,  # Must be True for /api/analytics
}
```

### Issue: Database Not Found
```python
# Use centralized DB_PATH
from app.config import DB_PATH
# Don't hardcode paths!
```

## 📚 Documentation Files

- `ARCHITECTURE_RESTRUCTURE.md` - Detailed architecture
- `MIGRATION_GUIDE.md` - Migration steps
- `ARCHITECTURE_DIAGRAMS.md` - Visual diagrams
- `RESTRUCTURE_SUMMARY.md` - Summary of changes
- `QUICK_REFERENCE.md` - This file

## 💡 Pro Tips

1. **Always use config.py** - Don't hardcode paths or settings
2. **Use feature flags** - Easy to enable/disable features
3. **Import from modules** - Not from individual files
4. **Check blueprints** - Each module has its own routes
5. **Test frequently** - Run tests after changes

## 🎯 Quick Wins

### Want to disable admin dashboard?
```python
# app/config.py
FEATURES = {
    'admin_dashboard_enabled': False,  # Set to False
}
```

### Want to change database location?
```python
# app/config.py
DB_PATH = DATA_DIR / "my_custom_db.db"
```

### Want to adjust confidence threshold?
```python
# app/config.py
CONFIDENCE_THRESHOLDS = {
    'high': 0.90,  # Increase from 0.85
    'medium': 0.70,
    'low': 0.50
}
```

---

**Keep this file handy for quick reference during development!**
