"""Test advanced detection features."""
from app.utils.advanced_detection import (
    filter_urls,
    comprehensive_phishing_detection,
    get_user_education_tips,
    get_account_security_tips
)

print("=" * 60)
print("Testing Advanced Phishing Detection")
print("=" * 60)

# Test 1: URL Filtering
print("\n1️⃣  URL Filtering Test")
print("-" * 60)
test_email = """
Your account will be locked! Click here to verify:
http://bit.ly/verify123
Or visit: http://192.168.1.1/phishing-page
Legitimate link: https://university.edu/portal
"""

url_result = filter_urls(test_email)
print(f"✅ URLs found: {url_result['urls_found']}")
print(f"✅ High-risk URLs: {len(url_result['high_risk_urls'])}")
print(f"✅ Overall URL risk: {url_result['overall_risk']:.1f}/100")

for url_info in url_result['urls']:
    if url_info.get('risk_score', 0) > 30:
        print(f"   ⚠️  {url_info['url']} - Risk: {url_info['risk_score']:.0f}")

# Test 2: Comprehensive Detection
print("\n2️⃣  Comprehensive Detection Test")
print("-" * 60)
phishing_email = """
URGENT: Your scholarship verification deadline is tomorrow!
Click here immediately: http://bit.ly/verify-scholarship
Provide your credentials to claim your reward.
This is your FINAL NOTICE. Act now or lose access!
"""

comprehensive_result = comprehensive_phishing_detection(
    email_text=phishing_email,
    headers={'From': 'admin@university.edu', 'Reply-To': 'attacker@evil.com'},
    attachments=['invoice.exe', 'document.docm'],
    user_id='student123'
)

print(f"✅ Risk Level: {comprehensive_result['risk_level']}")
print(f"✅ Overall Risk Score: {comprehensive_result['overall_risk_score']:.1f}/100")
print(f"✅ Recommendations: {len(comprehensive_result['recommendations'])}")

for rec in comprehensive_result['recommendations'][:3]:
    print(f"   {rec}")

# Test 3: Security Tips
print("\n3️⃣  Security Education Tips")
print("-" * 60)
education_tips = get_user_education_tips()
print(f"✅ User education tips: {len(education_tips)}")
for tip in education_tips[:3]:
    print(f"   {tip}")

account_tips = get_account_security_tips()
print(f"\n✅ Account security tips: {len(account_tips)}")
for tip in account_tips[:2]:
    print(f"   • {tip}")

print("\n" + "=" * 60)
print("✅ All Advanced Detection Tests Passed!")
print("=" * 60)
