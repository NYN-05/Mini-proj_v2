"""
End-to-End Functionality Test for EduShield
Tests the complete phishing detection pipeline
"""
import requests
import json

# Test emails
test_emails = [
    {
        "name": "High-Risk Phishing Email",
        "text": "URGENT ACTION REQUIRED! Your scholarship account has been suspended due to suspicious activity. Click here immediately to verify your credentials and restore access. This is your final warning - your account will be permanently deleted within 24 hours if you do not act now. Congratulations, you have also been selected for a special $500 reward!"
    },
    {
        "name": "Moderate Risk Email",
        "text": "Dear Student, Your exam results are now available. Please login to the student portal to view your results. The deadline for registration is approaching."
    },
    {
        "name": "Legitimate Email",
        "text": "Hello, This is a reminder about the upcoming faculty meeting on Friday at 2 PM in Room 301. Please review the agenda attached."
    }
]

def test_detection(email_data):
    """Test the /detect endpoint"""
    print(f"\n{'='*80}")
    print(f"Testing: {email_data['name']}")
    print(f"{'='*80}")
    
    url = "http://127.0.0.1:5000/detect"
    payload = {"email_text": email_data['text']}
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        
        data = response.json()
        
        # Display results
        print(f"\n✓ Classification: {data['classification']}")
        print(f"✓ Confidence: {data['confidence']*100:.2f}%")
        print(f"✓ ML Confidence: {data['ml_confidence']*100:.2f}%")
        print(f"✓ Urgency Score: {data['urgency_score']}/10")
        print(f"✓ Keywords Found: {', '.join(data['keywords'][:5])}")
        
        # Emotional Analysis
        ea = data.get('emotional_analysis', {})
        print(f"\n📊 Emotional Analysis:")
        print(f"   Hidden Meaning Score: {ea.get('hidden_meaning_score', 0)}/100")
        
        manip_risk = ea.get('manipulation_risk', {})
        print(f"   Manipulation Risk: {manip_risk.get('level', 'N/A')} (Score: {manip_risk.get('score', 0)})")
        
        sentiment = ea.get('sentiment', {})
        print(f"   Sentiment: {sentiment.get('label', 'N/A')} (Polarity: {sentiment.get('polarity', 0):.2f})")
        
        # Emotional scores
        emotional_scores = ea.get('emotional_scores', {})
        if emotional_scores:
            print(f"\n   Emotional Markers:")
            for emotion, scores in emotional_scores.items():
                if scores.get('score', 0) > 0:
                    print(f"      {emotion.capitalize()}: {scores.get('score', 0):.2f}/10 ({scores.get('count', 0)} instances)")
        
        # URL Analysis
        url_analysis = data.get('url_analysis', {})
        print(f"\n🔗 URL Analysis:")
        print(f"   URLs Found: {url_analysis.get('urls_found', 0)}")
        print(f"   Overall URL Risk: {url_analysis.get('overall_url_risk', 0)}/100")
        
        # Risk Factors
        risk_factors = data.get('risk_factors', [])
        if risk_factors:
            print(f"\n⚠️  Risk Factors ({len(risk_factors)}):")
            for i, factor in enumerate(risk_factors[:5], 1):
                print(f"   {i}. {factor}")
        
        print(f"\n✅ Test Passed: {email_data['name']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON Decode Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("EduShield End-to-End Functionality Test")
    print("="*80)
    
    # Test server connectivity
    try:
        response = requests.get("http://127.0.0.1:5000/")
        print("\n✅ Server is running and accessible")
    except:
        print("\n❌ Server is not accessible. Please start the Flask app first.")
        return
    
    # Run tests
    results = []
    for email in test_emails:
        result = test_detection(email)
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"Test Summary")
    print(f"{'='*80}")
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    if all(results):
        print(f"\n🎉 All tests passed! End-to-end functionality is working correctly.")
    else:
        print(f"\n⚠️  Some tests failed. Please review the output above.")


if __name__ == "__main__":
    main()
