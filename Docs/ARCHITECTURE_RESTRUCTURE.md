# EduShield - Restructured Architecture Documentation

## 📋 Overview

This document describes the restructured, modular architecture of EduShield designed to improve maintainability, scalability, and code organization.

## 🏗️ Project Structure

```
model_2/
├── app/
│   ├── __init__.py                 # Application package
│   ├── config.py                   # ⭐ Centralized configuration
│   ├── app.py                      # Legacy monolithic app (deprecated)
│   ├── app_new.py                  # ⭐ New modular app with blueprints
│   │
│   ├── core/                       # ⭐ PRIMARY DETECTION FEATURES
│   │   ├── __init__.py
│   │   ├── predictor.py            # ML model bundle and prediction logic
│   │   ├── explainer.py            # Explainability and highlighting
│   │   └── routes.py               # Core detection endpoints
│   │
│   ├── modules/                    # ⭐ TERTIARY & ADMINISTRATIVE FEATURES
│   │   ├── __init__.py
│   │   │
│   │   ├── analytics/              # Analytics & Data persistence
│   │   │   ├── __init__.py
│   │   │   ├── database.py         # SQLite database operations
│   │   │   └── routes.py           # Analytics API endpoints
│   │   │
│   │   ├── admin/                  # Administrative interfaces
│   │   │   ├── __init__.py
│   │   │   └── routes.py           # Admin dashboard routes
│   │   │
│   │   └── education/              # Security awareness content
│   │       ├── __init__.py
│   │       ├── tips.py             # Education tips and content
│   │       └── routes.py           # Education API endpoints
│   │
│   ├── utils/                      # ⚠️ LEGACY (to be deprecated)
│   │   ├── predictor.py            # Moved to app/core/
│   │   ├── explainer.py            # Moved to app/core/
│   │   └── advanced_detection.py   # Advanced phishing techniques
│   │
│   ├── templates/                  # HTML templates
│   │   ├── index.html              # Main detection interface
│   │   └── admin_dashboard.html    # Analytics dashboard
│   │
│   └── static/                     # Static assets
│       ├── css/
│       │   ├── style.css
│       │   └── admin_dashboard.css
│       └── js/
│           ├── main.js
│           └── admin_dashboard.js
│
├── models/                         # Trained ML models
│   ├── tfidf.pkl
│   ├── logistic.pkl
│   ├── nb.pkl
│   └── svm.pkl
│
├── data/                           # Data storage
│   └── edushield_analytics.db      # SQLite database
│
├── src/                            # Training scripts
│   └── train_models.py
│
├── tests/                          # Test suite
│   ├── test_predictor.py
│   └── test_advanced_features.py
│
├── requirements.txt                # Python dependencies
└── README.md                       # Main documentation
```

## 🎯 Architecture Principles

### 1. **Separation of Concerns**
- **Core Features**: Essential phishing detection (ML models, predictions)
- **Analytics Module**: Data logging, statistics, reporting (tertiary)
- **Admin Module**: Dashboard and administrative UI (low-usage)
- **Education Module**: Security awareness tips (supplementary)

### 2. **Modular Design**
- Each module has its own routes (Flask Blueprints)
- Independent database operations
- Feature flags for enabling/disabling modules

### 3. **Centralized Configuration**
- Single `config.py` file for all settings
- Easy to modify paths, thresholds, and features
- Environment-specific configurations

## 📦 Module Breakdown

### **app/config.py** - Configuration Module
```python
# All project settings in one place
PROJECT_ROOT          # Project paths
DB_PATH               # Database location
MODEL_FILES           # Model file paths
TFIDF_CONFIG          # ML parameters
DETECTION_WEIGHTS     # Risk scoring weights
FLASK_CONFIG          # Flask app settings
FEATURES              # Feature flags
```

### **app/core/** - Core Detection Module
**Purpose**: Primary phishing detection functionality

**Components**:
- `predictor.py`: ML model loading, ensemble prediction
- `explainer.py`: Keyword highlighting, risk factor extraction
- `routes.py`: Flask routes for `/detect` and `/detect/advanced`

**Endpoints**:
- `GET /` - Main detection interface
- `POST /detect` - Basic AI/ML detection
- `POST /detect/advanced` - Multi-technique detection

### **app/modules/analytics/** - Analytics Module
**Purpose**: Data persistence, statistics, and analytics (tertiary feature)

**Components**:
- `database.py`: SQLite operations, 6 analytics tables
- `routes.py`: Analytics API endpoints

**Endpoints**:
- `GET /api/analytics` - Comprehensive analytics data
- `GET /api/heatmap` - Attack heatmap
- `GET /api/user-awareness` - Usage statistics

### **app/modules/admin/** - Admin Module
**Purpose**: Administrative dashboard (low-usage feature)

**Components**:
- `routes.py`: Admin dashboard rendering

**Endpoints**:
- `GET /admin` - Admin dashboard interface

### **app/modules/education/** - Education Module
**Purpose**: Security awareness content (supplementary feature)

**Components**:
- `tips.py`: Security education content
- `routes.py`: Education API endpoints

**Endpoints**:
- `GET /api/security-tips` - Security awareness tips

## 🔄 Migration from Legacy App

### Old Architecture (Monolithic)
```python
# app.py - 235 lines, all features mixed
from app.utils.predictor import ...
from app.utils.explainer import ...
from app.database import ...
from app.utils.advanced_detection import ...

@app.route('/')
@app.route('/admin')
@app.route('/api/analytics')
@app.route('/api/security-tips')
@app.route('/detect')
```

### New Architecture (Modular)
```python
# app_new.py - 65 lines, blueprint-based
from app.core.routes import core_bp
from app.modules.analytics.routes import analytics_bp
from app.modules.admin.routes import admin_bp
from app.modules.education.routes import education_bp

app.register_blueprint(core_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(education_bp)
```

## 🚀 Usage

### Running the New Modular App
```bash
# Use the new modular architecture
python app/app_new.py

# Or with Flask CLI
export FLASK_APP=app.app_new:app
flask run
```

### Feature Flags
Enable/disable features in `app/config.py`:
```python
FEATURES = {
    'analytics_enabled': True,           # Enable analytics module
    'admin_dashboard_enabled': True,     # Enable admin dashboard
    'advanced_detection_enabled': True,  # Enable multi-technique detection
    'education_module_enabled': True,    # Enable security tips
    'behavior_analysis_enabled': True,   # Enable behavior analysis
    'threat_intelligence_enabled': True  # Enable threat intelligence
}
```

## 📊 Benefits of New Architecture

### 1. **Improved Maintainability**
- ✅ Clear separation between core and tertiary features
- ✅ Easy to locate and modify specific functionality
- ✅ Reduced cognitive load when working on code

### 2. **Reduced Clutter**
- ✅ Admin features isolated in dedicated module
- ✅ Analytics separated from core detection
- ✅ Education content in its own module

### 3. **Scalability**
- ✅ Easy to add new modules without touching core
- ✅ Independent testing of each module
- ✅ Can deploy modules separately if needed

### 4. **Better Testing**
- ✅ Unit tests can target specific modules
- ✅ Mock dependencies more easily
- ✅ Integration tests for each blueprint

### 5. **Configuration Management**
- ✅ All settings in one place (`config.py`)
- ✅ Easy to switch between environments
- ✅ Feature flags for conditional features

## 🔧 Development Workflow

### Adding a New Feature
1. Determine if it's core or tertiary
2. If tertiary, create new module under `app/modules/`
3. Create routes blueprint in module
4. Register blueprint in `app_new.py`
5. Add feature flag in `config.py`

### Modifying Core Detection
1. Edit files in `app/core/`
2. Update `predictor.py` for ML changes
3. Update `explainer.py` for explanation changes
4. Update `routes.py` for new endpoints

### Updating Analytics
1. Edit `app/modules/analytics/database.py` for schema changes
2. Edit `app/modules/analytics/routes.py` for new endpoints
3. Test with admin dashboard

## 🧪 Testing Strategy

### Core Module Tests
```python
# Test detection accuracy
from app.core import predict_phishing, ModelBundle

# Test explainability
from app.core import highlight_keywords, risk_factors_from_prediction
```

### Analytics Module Tests
```python
# Test database operations
from app.modules.analytics import init_db, log_prediction

# Test analytics endpoints
# GET /api/analytics
# GET /api/heatmap
```

### Education Module Tests
```python
# Test education content
from app.modules.education import get_user_education_tips

# Test education endpoints
# GET /api/security-tips
```

## 📝 Migration Checklist

- [x] Created `app/config.py` for centralized configuration
- [x] Created `app/core/` module for primary detection
- [x] Created `app/modules/analytics/` for data persistence
- [x] Created `app/modules/admin/` for dashboard
- [x] Created `app/modules/education/` for security tips
- [x] Created Flask blueprints for each module
- [x] Created `app_new.py` with blueprint registration
- [ ] Update import statements across project
- [ ] Deprecate `app/utils/` directory
- [ ] Update test suite for new structure
- [ ] Update deployment documentation
- [ ] Replace `app.py` with `app_new.py`

## 🔮 Future Enhancements

1. **API Module**: RESTful API with versioning
2. **Auth Module**: User authentication and authorization
3. **Reporting Module**: PDF report generation
4. **Notification Module**: Email/SMS alerts
5. **Integration Module**: Third-party service integrations

## 📚 Additional Resources

- [Flask Blueprints Documentation](https://flask.palletsprojects.com/en/2.0.x/blueprints/)
- [Application Factory Pattern](https://flask.palletsprojects.com/en/2.0.x/patterns/appfactories/)
- [Configuration Handling](https://flask.palletsprojects.com/en/2.0.x/config/)

---

**Note**: The legacy `app.py` is still functional for backward compatibility. Migrate to `app_new.py` for the improved modular architecture.
