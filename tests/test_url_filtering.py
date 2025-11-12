"""
Test URL Filtering Functionality
Tests the URL filtering and phishing detection capabilities.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.url_filter import (
    extract_urls, 
    is_ip_address_url, 
    is_url_shortener,
    has_suspicious_tld,
    check_homograph_attack,
    analyze_single_url,
    filter_urls,
    get_url_risk_summary
)


def test_extract_urls():
    """Test URL extraction from text."""
    print("\n1️⃣ Testing URL Extraction")
    print("=" * 60)
    
    test_text = """
    Dear user, please verify your account at https://example.com/verify
    and also check www.test-site.com for more info.
    Visit http://192.168.1.1/admin for account settings.
    """
    
    urls = extract_urls(test_text)
    print(f"Text: {test_text.strip()}")
    print(f"Extracted URLs: {urls}")
    print(f"✅ Found {len(urls)} URL(s)")


def test_ip_address_detection():
    """Test IP address URL detection."""
    print("\n2️⃣ Testing IP Address Detection")
    print("=" * 60)
    
    test_cases = [
        ("http://192.168.1.1/login", True),
        ("https://example.com", False),
        ("http://10.0.0.1/verify", True),
    ]
    
    for url, expected in test_cases:
        result = is_ip_address_url(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url}: IP-based = {result} (expected {expected})")


def test_url_shortener_detection():
    """Test URL shortener detection."""
    print("\n3️⃣ Testing URL Shortener Detection")
    print("=" * 60)
    
    test_cases = [
        ("https://bit.ly/abc123", True),
        ("http://t.co/xyz", True),
        ("https://example.com/page", False),
        ("https://tinyurl.com/test", True),
    ]
    
    for url, expected in test_cases:
        result = is_url_shortener(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url}: Shortener = {result} (expected {expected})")


def test_suspicious_tld():
    """Test suspicious TLD detection."""
    print("\n4️⃣ Testing Suspicious TLD Detection")
    print("=" * 60)
    
    test_cases = [
        ("http://example.tk", True),
        ("http://test.ml", True),
        ("http://example.com", False),
        ("http://site.xyz", True),
    ]
    
    for url, expected in test_cases:
        result = has_suspicious_tld(url)
        status = "✅" if result == expected else "❌"
        print(f"{status} {url}: Suspicious TLD = {result} (expected {expected})")


def test_single_url_analysis():
    """Test comprehensive single URL analysis."""
    print("\n5️⃣ Testing Single URL Analysis")
    print("=" * 60)
    
    test_urls = [
        "http://192.168.1.1/verify-account",
        "https://bit.ly/phishing123",
        "https://example.com/page",
        "http://malicious-site.tk/login",
    ]
    
    for url in test_urls:
        result = analyze_single_url(url)
        print(f"\nURL: {url}")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Risk Score: {result['risk_score']}/100")
        if result['issues']:
            print(f"  Issues:")
            for issue in result['issues']:
                print(f"    - {issue}")
        else:
            print(f"  Issues: None")


def test_filter_urls_comprehensive():
    """Test comprehensive URL filtering on email."""
    print("\n6️⃣ Testing Comprehensive URL Filtering")
    print("=" * 60)
    
    phishing_email = """
    URGENT: Your account has been suspended!
    
    Please verify your identity immediately by clicking here:
    http://192.168.1.1/account-verify
    
    Or use this link: https://bit.ly/verify123
    
    You can also visit http://paypal-secure.tk/login
    
    This is urgent and must be done within 24 hours.
    """
    
    print(f"Email:\n{phishing_email}")
    print("\nAnalysis Results:")
    print("-" * 60)
    
    result = filter_urls(phishing_email)
    
    print(f"URLs Found: {result['urls_found']}")
    print(f"High Risk URLs: {len(result['high_risk_urls'])}")
    print(f"Medium Risk URLs: {len(result['medium_risk_urls'])}")
    print(f"Overall Risk Score: {result['overall_risk']}/100")
    print(f"Has Suspicious URLs: {result['has_suspicious_urls']}")
    
    if result['high_risk_urls']:
        print("\n⚠️ HIGH RISK URLs:")
        for url_info in result['high_risk_urls']:
            print(f"  - {url_info['url']}")
            print(f"    Risk Score: {url_info['risk_score']}/100")
            print(f"    Issues: {', '.join(url_info['issues'])}")
    
    if result['medium_risk_urls']:
        print("\n⚠️ MEDIUM RISK URLs:")
        for url_info in result['medium_risk_urls']:
            print(f"  - {url_info['url']}")
            print(f"    Risk Score: {url_info['risk_score']}/100")
            print(f"    Issues: {', '.join(url_info['issues'])}")
    
    # Get risk summary
    print("\nRisk Summary:")
    print("-" * 60)
    summary = get_url_risk_summary(result)
    for item in summary:
        print(f"  {item}")


def test_legitimate_email():
    """Test URL filtering on legitimate email."""
    print("\n7️⃣ Testing Legitimate Email")
    print("=" * 60)
    
    legitimate_email = """
    Hello,
    
    Thank you for your interest in our services. You can find more 
    information on our official website:
    
    https://www.university.edu/admissions
    
    Feel free to contact us if you have any questions.
    
    Best regards,
    University Admissions Team
    """
    
    print(f"Email:\n{legitimate_email}")
    print("\nAnalysis Results:")
    print("-" * 60)
    
    result = filter_urls(legitimate_email)
    
    print(f"URLs Found: {result['urls_found']}")
    print(f"High Risk URLs: {len(result['high_risk_urls'])}")
    print(f"Overall Risk Score: {result['overall_risk']}/100")
    print(f"Has Suspicious URLs: {result['has_suspicious_urls']}")
    
    if result['urls']:
        print("\nURL Details:")
        for url_info in result['urls']:
            print(f"  - {url_info['url']}")
            print(f"    Risk Level: {url_info['risk_level']}")
            print(f"    Risk Score: {url_info['risk_score']}/100")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🔍 URL FILTERING TEST SUITE")
    print("=" * 60)
    
    test_extract_urls()
    test_ip_address_detection()
    test_url_shortener_detection()
    test_suspicious_tld()
    test_single_url_analysis()
    test_filter_urls_comprehensive()
    test_legitimate_email()
    
    print("\n" + "=" * 60)
    print("✅ All URL Filtering Tests Completed!")
    print("=" * 60)
