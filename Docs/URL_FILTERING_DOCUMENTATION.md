# 🔗 URL Filtering Feature Documentation

## Overview

The URL filtering feature examines links embedded in emails to detect phishing attempts. Phishing emails commonly include malicious URLs designed to:
- Trick users into providing login credentials
- Serve malware
- Direct users to fake websites (lookalike/homograph attacks)

## How It Works

### Detection Techniques

The URL filtering module analyzes URLs using multiple techniques:

#### 1. **IP Address Detection**
- **Risk Level**: HIGH (30 points)
- **What**: Detects URLs using IP addresses instead of domain names
- **Why Suspicious**: Legitimate websites use domain names, not raw IP addresses
- **Example**: `http://192.168.1.1/login` ⚠️

#### 2. **URL Shortener Detection**
- **Risk Level**: MEDIUM-HIGH (25 points)
- **What**: Identifies known URL shortening services
- **Why Suspicious**: Shorteners hide the actual destination, common in phishing
- **Services Detected**: bit.ly, t.co, tinyurl.com, goo.gl, ow.ly, is.gd, buff.ly
- **Example**: `https://bit.ly/verify123` ⚠️

#### 3. **Suspicious TLD Detection**
- **Risk Level**: MEDIUM (20 points)
- **What**: Flags suspicious top-level domains
- **Why Suspicious**: Free/rarely-used TLDs often used for temporary phishing sites
- **TLDs Flagged**: .tk, .ml, .ga, .cf, .gq, .xyz, .top, .work
- **Example**: `http://phishing-site.tk` ⚠️

#### 4. **Homograph Attack Detection**
- **Risk Level**: HIGH (35 points)
- **What**: Detects lookalike characters from different alphabets
- **Why Suspicious**: Creates domains that look legitimate but aren't
- **Characters Flagged**: Cyrillic, Greek characters that resemble Latin letters
- **Example**: `http://paypaI.com` (capital i instead of lowercase L) ⚠️

#### 5. **Excessive Subdomains**
- **Risk Level**: MEDIUM (15 points)
- **What**: Flags URLs with more than 3 subdomain levels
- **Why Suspicious**: Used to make URLs look legitimate
- **Example**: `http://secure.verify.account.paypal-login.com` ⚠️

#### 6. **Suspicious Path Keywords**
- **Risk Level**: LOW-MEDIUM (10 points)
- **What**: Checks for common phishing-related keywords in URL path
- **Keywords**: login, signin, verify, account, update, confirm, secure, banking, suspended, locked
- **Example**: `http://example.com/verify-account` ⚠️

## Integration with Main Detection

URL filtering is **automatically integrated** into the main `/detect` endpoint:

### Detection Flow
```
Email Text
    ↓
┌─────────────────────────────────────┐
│  1. ML Model Analysis (70% weight) │
│     - Logistic Regression           │
│     - Naive Bayes                   │
│     - SVM                            │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. URL Filtering (30% weight)      │
│     - Extract all URLs              │
│     - Analyze each URL              │
│     - Calculate risk scores         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Combined Analysis                │
│     - Merge ML + URL scores         │
│     - Adjust classification         │
│     - Generate risk factors         │
└─────────────────────────────────────┘
    ↓
  Final Result
```

### Scoring Algorithm

```python
# ML models contribute 70%
ml_weight = 0.7

# URL analysis contributes 30%
url_risk_weight = 0.3

# Combined confidence
combined_confidence = (ml_weight × ml_confidence) + 
                     (url_risk_weight × url_risk_score)

# Special case: High-risk URLs detected
if high_risk_urls AND overall_url_risk >= 50:
    combined_confidence = max(combined_confidence, 0.7)
    classification = 'PHISHING'
```

## API Response Format

### Request
```json
POST /detect
{
    "email_text": "Verify your account at http://192.168.1.1/verify",
    "institution": "My University"
}
```

### Response
```json
{
    "classification": "PHISHING",
    "confidence": 0.82,
    "ml_confidence": 0.75,
    "model_probs": {
        "logistic": 0.78,
        "nb": 0.72,
        "svm": 0.76
    },
    "urgency_score": 8.5,
    "keywords": ["verify", "account"],
    "highlighted_text": "...",
    "risk_factors": [
        "High-risk keywords: verify, account",
        "Urgency detected (score 8.5/10)",
        "Found 1 URL(s) in email",
        "⚠️ 1 HIGH RISK URL(s) detected",
        "  - http://192.168.1.1/verify: Uses IP address, Path contains suspicious keywords"
    ],
    "url_analysis": {
        "urls_found": 1,
        "high_risk_urls": 1,
        "medium_risk_urls": 0,
        "overall_url_risk": 40.0,
        "suspicious_urls": true,
        "url_details": [
            {
                "url": "http://192.168.1.1/verify",
                "risk_score": 40,
                "risk_level": "MEDIUM",
                "issues": [
                    "Uses IP address instead of domain name",
                    "Path contains suspicious keywords"
                ]
            }
        ]
    }
}
```

## Usage Examples

### Example 1: Phishing Email with IP Address
```python
email = "Click here to verify: http://192.168.1.1/account"

# Result:
# - URL detected: http://192.168.1.1/account
# - Risk: MEDIUM (40/100)
# - Issues: IP address, suspicious path
# - Final classification: PHISHING
```

### Example 2: URL Shortener in Email
```python
email = "Important update: https://bit.ly/update123"

# Result:
# - URL detected: https://bit.ly/update123
# - Risk: MEDIUM (25/100)
# - Issues: URL shortening service
# - Contributes to phishing likelihood
```

### Example 3: Legitimate Email
```python
email = "Visit our website: https://university.edu/admissions"

# Result:
# - URL detected: https://university.edu/admissions
# - Risk: SAFE (0/100)
# - Issues: None
# - Normal email processing
```

## Risk Levels

| Risk Score | Risk Level | Action |
|------------|------------|--------|
| 50-100 | HIGH | Strong phishing indicator |
| 30-49 | MEDIUM | Suspicious, increases phishing likelihood |
| 10-29 | LOW | Minor concerns, monitored |
| 0-9 | SAFE | No issues detected |

## Testing

Run the URL filtering test suite:

```bash
python tests/test_url_filtering.py
```

### Test Coverage
- ✅ URL extraction from text
- ✅ IP address detection
- ✅ URL shortener detection
- ✅ Suspicious TLD detection
- ✅ Single URL comprehensive analysis
- ✅ Full email URL filtering
- ✅ Legitimate email handling

## Configuration

URL filtering settings are in `app/config.py`:

```python
# Suspicious top-level domains
SUSPICIOUS_TLDS = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work']

# URL shortening services
URL_SHORTENERS = ['bit.ly', 't.co', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly']

# Dangerous file extensions (for attachment scanning)
DANGEROUS_EXTENSIONS = ['.exe', '.scr', '.bat', '.cmd', '.vbs', '.js', '.jar', '.docm', '.xlsm', '.pptm']
```

## Benefits

✅ **Enhanced Detection**: Catches phishing that ML models might miss  
✅ **Real-time Analysis**: Instant URL risk assessment  
✅ **Transparent Results**: Detailed explanations of URL issues  
✅ **Configurable**: Easy to add new suspicious patterns  
✅ **Lightweight**: No external API calls required  
✅ **Educational**: Users learn what makes URLs suspicious  

## Limitations

⚠️ **No URL Reputation Database**: Doesn't check against known malicious URL databases  
⚠️ **Static Analysis Only**: Doesn't visit URLs to check actual content  
⚠️ **Pattern-Based**: May flag legitimate URLs with suspicious patterns  
⚠️ **No HTTPS Validation**: Doesn't verify SSL certificates  

## Future Enhancements

1. **URL Reputation API Integration**: Check URLs against threat intelligence databases
2. **Real-time URL Scanning**: Safe browsing API integration
3. **SSL Certificate Validation**: Verify HTTPS certificates
4. **Domain Age Checking**: Flag newly registered domains
5. **Redirect Chain Analysis**: Follow URL redirects safely
6. **QR Code Analysis**: Detect URLs in embedded QR codes

## Files

- `app/core/url_filter.py` - URL filtering implementation
- `app/core/routes.py` - Integration with detection endpoint
- `tests/test_url_filtering.py` - Test suite
- `app/config.py` - Configuration settings

---

**Status**: ✅ URL Filtering Active  
**Integration**: Automatic (30% weight in final score)  
**Performance**: Real-time, no external dependencies
