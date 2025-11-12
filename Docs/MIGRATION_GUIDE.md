# 🔄 EduShield Architecture Migration Guide

## Quick Start

### For New Developers
Start with the new modular architecture:
```bash
python app/app_new.py
```

### For Existing Deployments
The legacy `app.py` will continue to work. Migrate when ready.

## 📋 What Changed?

### Before (Monolithic)
```
app/
├── app.py                    # 235 lines, all features
├── database.py               # Mixed with app logic
├── utils/
│   ├── predictor.py
│   ├── explainer.py
│   └── advanced_detection.py # Everything in one file
```

### After (Modular)
```
app/
├── config.py                 # ⭐ NEW: Centralized config
├── app_new.py                # ⭐ NEW: Modular app (65 lines)
├── core/                     # ⭐ NEW: Core detection
│   ├── predictor.py
│   ├── explainer.py
│   └── routes.py
├── modules/                  # ⭐ NEW: Tertiary features
│   ├── analytics/
│   │   ├── database.py
│   │   └── routes.py
│   ├── admin/
│   │   └── routes.py
│   └── education/
│       ├── tips.py
│       └── routes.py
```

## 🔧 Migration Steps

### Step 1: Update Your Imports

#### Old Import Pattern
```python
from app.utils.predictor import ModelBundle, predict_phishing
from app.utils.explainer import highlight_keywords
from app.database import init_db, log_prediction
from app.utils.advanced_detection import get_user_education_tips
```

#### New Import Pattern
```python
# Core detection
from app.core import ModelBundle, predict_phishing
from app.core import highlight_keywords, risk_factors_from_prediction

# Analytics
from app.modules.analytics import init_db, log_prediction, get_analytics_data

# Education
from app.modules.education import get_user_education_tips

# Configuration
from app.config import PROJECT_ROOT, DB_PATH, FEATURES
```

### Step 2: Update Application Startup

#### Old Way
```python
from app.app import app

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

#### New Way
```python
from app.app_new import app

if __name__ == '__main__':
    app.run()  # Uses config.py settings
```

### Step 3: Enable/Disable Features

Edit `app/config.py`:
```python
FEATURES = {
    'analytics_enabled': True,           # Toggle analytics
    'admin_dashboard_enabled': True,     # Toggle admin panel
    'advanced_detection_enabled': True,  # Toggle advanced detection
    'education_module_enabled': True,    # Toggle education tips
}
```

### Step 4: Update Configuration

#### Old Way (Hardcoded)
```python
DB_PATH = Path(__file__).parent.parent / "data" / "edushield_analytics.db"
MODELS_DIR = root / 'models'
```

#### New Way (Centralized)
```python
from app.config import DB_PATH, MODELS_DIR, MODEL_FILES
# All paths configured in one place
```

## 🧪 Testing Your Migration

### Test Core Detection
```python
from app.core import ModelBundle, predict_phishing
from app.config import PROJECT_ROOT

# Load models
bundle = ModelBundle(PROJECT_ROOT)

# Test prediction
result = predict_phishing("Verify your account urgently!", bundle)
print(result['classification'])  # Should work
```

### Test Analytics
```python
from app.modules.analytics import init_db, log_prediction

# Initialize database
init_db()

# Log a test prediction
log_prediction(
    classification='PHISHING',
    confidence=0.95,
    email_text='Test email',
    model_scores={'logistic': 0.9, 'nb': 0.85, 'svm': 0.92},
    institution='Test Institution'
)
```

### Test Flask App
```bash
# Start the new app
python app/app_new.py

# Test endpoints
curl http://localhost:5000/
curl http://localhost:5000/api/analytics
curl http://localhost:5000/api/security-tips
```

## 📦 Module-by-Module Guide

### Core Module (`app/core/`)
**What**: Essential phishing detection functionality  
**When to use**: Any ML prediction or explanation task  
**Key files**:
- `predictor.py` - Model loading, predictions
- `explainer.py` - Keyword highlighting, risk factors
- `routes.py` - `/detect` endpoints

**Example**:
```python
from app.core import ModelBundle, predict_phishing, highlight_keywords

bundle = ModelBundle()
pred = predict_phishing(email_text, bundle)
highlighted = highlight_keywords(email_text, pred['keywords'])
```

### Analytics Module (`app/modules/analytics/`)
**What**: Data logging, statistics, reporting (tertiary)  
**When to use**: Tracking predictions, generating reports  
**Key files**:
- `database.py` - SQLite operations
- `routes.py` - `/api/analytics` endpoints

**Example**:
```python
from app.modules.analytics import log_prediction, get_analytics_data

# Log prediction
log_prediction(classification, confidence, email_text, model_scores)

# Get analytics
analytics = get_analytics_data(institution='Test Univ', days=30)
```

### Admin Module (`app/modules/admin/`)
**What**: Administrative dashboard (low-usage)  
**When to use**: Viewing analytics dashboard  
**Key files**:
- `routes.py` - `/admin` dashboard route

**Example**:
```python
# Visit in browser
# http://localhost:5000/admin
```

### Education Module (`app/modules/education/`)
**What**: Security awareness tips (supplementary)  
**When to use**: Displaying security education content  
**Key files**:
- `tips.py` - Education content
- `routes.py` - `/api/security-tips` endpoint

**Example**:
```python
from app.modules.education import get_user_education_tips

tips = get_user_education_tips()
# Returns list of security awareness tips
```

## 🚨 Common Migration Issues

### Issue 1: Import Errors
**Problem**: `ImportError: cannot import name 'predict_phishing' from 'app.utils.predictor'`

**Solution**: Update import to use new location:
```python
from app.core import predict_phishing  # NEW
```

### Issue 2: Config Not Found
**Problem**: `AttributeError: module 'app' has no attribute 'config'`

**Solution**: Import config explicitly:
```python
from app.config import DB_PATH, FEATURES
```

### Issue 3: Blueprint Not Registered
**Problem**: `404 Not Found` for `/api/analytics`

**Solution**: Check feature flags in `app/config.py`:
```python
FEATURES = {
    'analytics_enabled': True,  # Must be True
}
```

### Issue 4: Database Path Wrong
**Problem**: `sqlite3.OperationalError: unable to open database file`

**Solution**: Use centralized config:
```python
from app.config import DB_PATH
# DB_PATH is automatically set correctly
```

## 📊 Comparison Table

| Aspect | Old (Monolithic) | New (Modular) |
|--------|-----------------|---------------|
| **Main file** | `app.py` (235 lines) | `app_new.py` (65 lines) |
| **Configuration** | Scattered | `config.py` (centralized) |
| **Core detection** | `app/utils/` | `app/core/` |
| **Analytics** | `app/database.py` | `app/modules/analytics/` |
| **Education** | Inside `advanced_detection.py` | `app/modules/education/` |
| **Routes** | All in `app.py` | Blueprints per module |
| **Feature flags** | None | `config.FEATURES` |
| **Testability** | Difficult | Easy (modular) |
| **Maintainability** | Low | High |

## ✅ Migration Checklist

Use this checklist to ensure complete migration:

- [ ] **Install dependencies** (no changes needed)
- [ ] **Update imports** in your custom code
- [ ] **Test core detection** - Verify ML predictions work
- [ ] **Test analytics** - Check database logging
- [ ] **Test admin dashboard** - Verify charts render
- [ ] **Test education API** - Check tips endpoint
- [ ] **Update startup script** - Use `app_new.py`
- [ ] **Configure features** - Set feature flags in `config.py`
- [ ] **Run test suite** - Ensure all tests pass
- [ ] **Update documentation** - Reflect new structure
- [ ] **Deploy to production** - Use new modular app

## 🎯 Best Practices

### 1. Use Feature Flags
```python
from app.config import FEATURES

if FEATURES['analytics_enabled']:
    log_prediction(...)
```

### 2. Import from Modules, Not Files
```python
# ❌ Bad
from app.core.predictor import predict_phishing

# ✅ Good
from app.core import predict_phishing
```

### 3. Use Centralized Config
```python
# ❌ Bad
DB_PATH = "data/edushield.db"

# ✅ Good
from app.config import DB_PATH
```

### 4. Keep Modules Independent
```python
# ❌ Bad - analytics importing from education
from app.modules.education import get_tips

# ✅ Good - use shared utilities if needed
from app.utils import shared_function
```

## 📚 Additional Resources

- **Architecture Docs**: `ARCHITECTURE_RESTRUCTURE.md`
- **Configuration Guide**: `app/config.py` (comments)
- **Blueprint Tutorial**: Flask official docs
- **Testing Guide**: `tests/` directory

## 💡 Need Help?

1. Check `ARCHITECTURE_RESTRUCTURE.md` for detailed structure
2. Review `app/config.py` for all settings
3. Look at blueprint examples in `app/*/routes.py`
4. Run tests to verify changes: `pytest tests/`

---

**Recommendation**: Start using `app_new.py` for new development. The modular structure will make your code more maintainable and easier to extend.
