"""
Security Education and Awareness Tips
Provides educational content for users to improve cybersecurity awareness.
"""
from typing import List


def get_user_education_tips() -> List[str]:
    """Return cybersecurity awareness tips for users.
    
    Returns:
        List of user-friendly security education tips with emojis.
    """
    return [
        "🎓 **Verify Sender**: Always check the sender's email address carefully",
        "🔗 **Hover Before Click**: Hover over links to preview the actual URL",
        "📎 **Be Cautious**: Don't open unexpected attachments, even from known senders",
        "🔒 **Check for HTTPS**: Legitimate sites use secure connections (https://)",
        "⚠️ **Watch for Urgency**: Phishing emails create false urgency to rush you",
        "🏢 **Use Official Channels**: Contact organizations through their official website/phone",
        "🔐 **Enable MFA**: Use multi-factor authentication on all accounts",
        "💪 **Strong Passwords**: Use unique, complex passwords for each account",
        "🔄 **Keep Updated**: Regularly update software and security patches",
        "📢 **Report Suspicious**: Report phishing attempts to IT security team"
    ]


def get_account_security_tips() -> List[str]:
    """Return account security recommendations.
    
    Returns:
        List of account security best practices.
    """
    return [
        "Enable multi-factor authentication (MFA) on all accounts",
        "Use a password manager for strong, unique passwords",
        "Regularly review account activity and login history",
        "Set up security alerts for unusual account access",
        "Never share passwords or authentication codes",
        "Use biometric authentication when available",
        "Be cautious of password reset emails you didn't request"
    ]


def get_patch_management_tips() -> List[str]:
    """Return patch management recommendations.
    
    Returns:
        List of software update and patch management best practices.
    """
    return [
        "Enable automatic updates for operating system and applications",
        "Regularly check for and install security patches",
        "Keep antivirus and anti-malware software up to date",
        "Update browser and browser extensions regularly",
        "Remove or disable unused software to reduce attack surface",
        "Subscribe to security bulletins for critical software you use"
    ]


def get_all_security_tips() -> dict:
    """Get all security tips organized by category.
    
    Returns:
        Dictionary with categorized security tips.
    """
    return {
        'user_education': get_user_education_tips(),
        'account_security': get_account_security_tips(),
        'patch_management': get_patch_management_tips()
    }
