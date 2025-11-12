"""
URL Filtering Module
Examines URLs in emails for phishing indicators.

Phishing emails commonly include embedded links that point toward phishing pages.
These pages could be designed to trick the user into handing over their login 
credentials or may serve malware to the user.

URL filtering involves examining the links included in an email for likely 
phishing pages. This includes:
- Known malicious URLs
- Lookalike URLs (homograph attacks)
- Suspicious URL structures
- URL shorteners
- IP-based URLs
- Suspicious TLDs
"""

import re
from urllib.parse import urlparse
from typing import List, Dict, Tuple
from app.config import SUSPICIOUS_TLDS, URL_SHORTENERS
import unicodedata
import html
import socket

try:
    import requests
except Exception:
    requests = None


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text.
    
    Args:
        text: Email content or text to analyze
        
    Returns:
        List of URLs found in the text
    """
    # Pattern to match URLs (http, https, ftp, and bare domains)
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    
    # Also look for www. patterns without protocol
    www_pattern = r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    www_urls = re.findall(www_pattern, text, re.IGNORECASE)
    urls.extend(['http://' + url for url in www_urls])
    
    return list(set(urls))  # Remove duplicates


def is_ip_address_url(url: str) -> bool:
    """Check if URL uses IP address instead of domain name.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL uses IP address (suspicious)
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc or parsed.path.split('/')[0]
        # Check for IPv4 pattern
        ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        return bool(re.match(ip_pattern, hostname))
    except:
        return False


def is_url_shortener(url: str) -> bool:
    """Check if URL uses a URL shortening service.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is from a known shortener service
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(shortener in domain for shortener in URL_SHORTENERS)
    except:
        return False


def has_suspicious_tld(url: str) -> bool:
    """Check if URL has a suspicious top-level domain.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL has suspicious TLD
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(domain.endswith(tld) for tld in SUSPICIOUS_TLDS)
    except:
        return False


def check_homograph_attack(url: str) -> bool:
    """Check for homograph/lookalike character attacks.
    
    Homograph attacks use similar-looking characters from different alphabets
    to create lookalike domains (e.g., replacing 'o' with Cyrillic 'о').
    
    Args:
        url: URL to check
        
    Returns:
        True if suspicious lookalike characters detected
    """
    # Improved homograph detection:
    # - Normalize Unicode (NFKC)
    # - Flag punycode (xn--)
    # - Flag presence of non-ASCII characters and mixing of scripts
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        if not domain:
            return False

        # punycode indicator
        if domain.startswith('xn--') or '.xn--' in domain:
            return True

        # Normalize and check for non-ascii
        norm = unicodedata.normalize('NFKC', domain)
        if all(ord(c) < 128 for c in norm):
            return False

        # Heuristic: if domain contains characters from multiple Unicode blocks,
        # flag as potential homograph. We approximate by checking Unicode name prefixes.
        scripts = set()
        for ch in norm:
            if ord(ch) < 128:
                scripts.add('ASCII')
                continue
            try:
                name = unicodedata.name(ch)
                block = name.split(' ')[0]
                scripts.add(block)
            except ValueError:
                scripts.add('UNKNOWN')

        return len(scripts) > 1
    except Exception:
        return False


def resolve_shortener(url: str, timeout: float = 3.0) -> str:
    """Attempt to resolve a shortened URL to its final destination.

    This will perform a HEAD request and follow redirects if `requests` is
    available. If not available or network fails, returns the original URL.
    """
    if requests is None:
        return url
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        return resp.url or url
    except Exception:
        return url


def has_excessive_subdomains(url: str, threshold: int = 3) -> bool:
    """Check if URL has excessive number of subdomains.
    
    Args:
        url: URL to check
        threshold: Maximum normal subdomain count
        
    Returns:
        True if subdomain count exceeds threshold
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        subdomain_count = domain.count('.')
        return subdomain_count > threshold
    except:
        return False


def check_suspicious_path(url: str) -> bool:
    """Check for suspicious path patterns.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL path contains suspicious patterns
    """
    suspicious_patterns = [
        'login', 'signin', 'verify', 'account', 'update',
        'confirm', 'secure', 'banking', 'paypal', 'ebay',
        'amazon', 'suspended', 'locked', 'unusual'
    ]
    
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        full_path = path + query
        
        return any(pattern in full_path for pattern in suspicious_patterns)
    except:
        return False


def analyze_single_url(url: str) -> Dict:
    """Perform comprehensive analysis on a single URL.
    
    Args:
        url: URL to analyze
        
    Returns:
        Dictionary with analysis results and risk score
    """
    issues = []
    risk_score = 0
    
    # Check for IP address (high risk)
    if is_ip_address_url(url):
        issues.append('Uses IP address instead of domain name')
        risk_score += 30
    
    # Check for URL shortener (medium-high risk)
    if is_url_shortener(url):
        issues.append('Uses URL shortening service')
        risk_score += 25
    
    # Check for suspicious TLD (medium risk)
    if has_suspicious_tld(url):
        issues.append('Uses suspicious top-level domain')
        risk_score += 20
    
    # Try to resolve shorteners first to inspect final domain
    resolved = resolve_shortener(url)
    if resolved and resolved != url:
        url_to_check = resolved
    else:
        url_to_check = url

    # Check for homograph attack (high risk)
    if check_homograph_attack(url_to_check):
        issues.append('Contains lookalike characters (homograph attack)')
        risk_score += 35
    
    # Check for excessive subdomains (medium risk)
    if has_excessive_subdomains(url):
        issues.append('Has excessive number of subdomains')
        risk_score += 15
    
    # Check for suspicious path (low-medium risk)
    if check_suspicious_path(url):
        issues.append('Path contains suspicious keywords')
        risk_score += 10
    
    # Determine risk level
    if risk_score >= 50:
        risk_level = 'HIGH'
    elif risk_score >= 30:
        risk_level = 'MEDIUM'
    elif risk_score >= 10:
        risk_level = 'LOW'
    else:
        risk_level = 'SAFE'
    
    return {
        'url': url,
        'risk_score': min(risk_score, 100),
        'risk_level': risk_level,
        'issues': issues
    }


def filter_urls(email_text: str) -> Dict:
    """Filter and analyze all URLs in email text.
    
    Args:
        email_text: Email content to analyze
        
    Returns:
        Dictionary containing URL analysis results
    """
    urls = extract_urls(email_text)
    
    if not urls:
        return {
            'urls_found': 0,
            'urls': [],
            'high_risk_urls': [],
            'medium_risk_urls': [],
            'overall_risk': 0,
            'has_suspicious_urls': False
        }
    
    # Analyze each URL
    url_analyses = [analyze_single_url(url) for url in urls]
    
    # Categorize by risk
    high_risk = [u for u in url_analyses if u['risk_level'] == 'HIGH']
    medium_risk = [u for u in url_analyses if u['risk_level'] == 'MEDIUM']
    
    # Calculate overall risk
    if url_analyses:
        overall_risk = sum(u['risk_score'] for u in url_analyses) / len(url_analyses)
    else:
        overall_risk = 0
    
    return {
        'urls_found': len(urls),
        'urls': url_analyses,
        'high_risk_urls': high_risk,
        'medium_risk_urls': medium_risk,
        'overall_risk': round(overall_risk, 2),
        'has_suspicious_urls': len(high_risk) > 0 or len(medium_risk) > 0
    }


def get_url_risk_summary(url_analysis: Dict) -> List[str]:
    """Generate human-readable risk summary from URL analysis.
    
    Args:
        url_analysis: Result from filter_urls()
        
    Returns:
        List of risk factor descriptions
    """
    risk_factors = []
    
    if url_analysis['urls_found'] == 0:
        return ['No URLs detected in email']
    
    risk_factors.append(f"Found {url_analysis['urls_found']} URL(s) in email")
    
    if url_analysis['high_risk_urls']:
        risk_factors.append(f"⚠️ {len(url_analysis['high_risk_urls'])} HIGH RISK URL(s) detected")
        for url_info in url_analysis['high_risk_urls']:
            risk_factors.append(f"  - {url_info['url']}: {', '.join(url_info['issues'])}")
    
    if url_analysis['medium_risk_urls']:
        risk_factors.append(f"⚠️ {len(url_analysis['medium_risk_urls'])} MEDIUM RISK URL(s) detected")
        for url_info in url_analysis['medium_risk_urls']:
            risk_factors.append(f"  - {url_info['url']}: {', '.join(url_info['issues'])}")
    
    if url_analysis['overall_risk'] >= 30:
        risk_factors.append(f"Overall URL risk score: {url_analysis['overall_risk']}/100")
    
    return risk_factors


def url_features_from_text(text: str) -> List[float]:
    """Extract numeric URL-derived features from an email text.
        Returns features in the following order:
            [has_shortener (0/1), uses_ip (0/1), suspicious_tld_count,
             homograph_count, avg_subdomain_count, path_suspicious_count, num_urls,
             anchor_mismatch_count]
    """
    urls = extract_urls(text)
    if not urls:
                return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    shortener_flag = 0
    ip_flag = 0
    suspicious_tld_count = 0
    homograph_count = 0
    subdomain_counts = []
    path_suspicious_count = 0

    for url in urls:
        if is_url_shortener(url):
            shortener_flag = 1
        if is_ip_address_url(url):
            ip_flag = 1
        # resolve shortener to get final domain for better TLD/homograph checks
        final_url = resolve_shortener(url)
        if has_suspicious_tld(final_url):
            suspicious_tld_count += 1
        if check_homograph_attack(final_url):
            homograph_count += 1
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path.split('/')[0]
            subdomain_counts.append(domain.count('.'))
            if check_suspicious_path(url):
                path_suspicious_count += 1
        except Exception:
            subdomain_counts.append(0)

    avg_subdomains = float(sum(subdomain_counts) / max(1, len(subdomain_counts)))
    # Anchor href vs display text mismatches
    anchor_mismatch = 0
    try:
        anchors = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, flags=re.IGNORECASE|re.DOTALL)
        for href, display in anchors:
            href_domain = urlparse(href).netloc
            display_unescaped = html.unescape(display)
            found = re.search(r'(https?://)?([\w\.-]+\.[a-zA-Z]{2,})', display_unescaped)
            if found:
                disp_domain = found.group(2).lower()
                if href_domain and disp_domain and disp_domain not in href_domain.lower():
                    anchor_mismatch += 1
    except Exception:
        anchor_mismatch = 0

    return [
        float(shortener_flag),
        float(ip_flag),
        float(suspicious_tld_count),
        float(homograph_count),
        float(avg_subdomains),
        float(path_suspicious_count),
        float(len(urls)),
        float(anchor_mismatch)
    ]
