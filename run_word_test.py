from app.detector import word_level_analysis

text = "Dear student, your scholarship verification is urgent. Click http://bit.ly/abc to verify your account now. Contact admin@example.edu"
mb = None  # Avoid loading ML models for quick smoke test
res = word_level_analysis(text, mb)
print('Tokens analyzed:', len(res))
for r in res:
    print(r)
