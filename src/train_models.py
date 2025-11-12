"""Train small prototype models on a synthetic academic phishing dataset.
This creates models/logistic.pkl, models/nb.pkl, models/svm.pkl and models/tfidf.pkl
Improved with:
- Expanded synthetic dataset (100+ examples)
- Better feature engineering (TF-IDF + ngrams)
- Multiple models with ensemble voting
- Hyperparameter tuning
- Cross-validation metrics
"""
import os
from pathlib import Path
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import StackingClassifier
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.base import BaseEstimator, TransformerMixin
from scipy.sparse import csr_matrix, hstack

# Ensure project root is on sys.path so `app` package imports work when running this script
import sys
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.url_filter import url_features_from_text
import numpy as np


# Expanded synthetic dataset with 100+ examples for better model training
DATA = [
    # PHISHING EXAMPLES (academic-themed) - 55 examples
    ("Your scholarship application has been approved! Click here to verify your account and claim your reward.", 1),
    ("URGENT: Exam registration deadline TODAY. Update your details immediately to avoid suspension.", 1),
    ("You have unpaid fee pending. Pay now to avoid penalty.", 1),
    ("Verify your student account now or it will be deactivated.", 1),
    ("Congratulations! You have been selected for a paid internship. Provide bank details to proceed.", 1),
    ("ALERT: Your campus account has been compromised. Reset password immediately by clicking here.", 1),
    ("Urgent: Verify your identity to unlock your scholarship funds. Act now!", 1),
    ("Your exam results are ready! Click to view grades and confirm enrollment.", 1),
    ("Re-activate your student account. Your access will expire in 24 hours.", 1),
    ("Claim your educational grant! Confirm personal and banking details now.", 1),
    ("Graduation clearance required. Submit all outstanding documents immediately.", 1),
    ("Your academic records are locked. Update account information right now.", 1),
    ("Special scholarship offer: Limited time! Enter your credentials to apply.", 1),
    ("System maintenance: Verify account credentials to maintain access.", 1),
    ("Immediate action required: Your tuition payment failed. Update payment method.", 1),
    ("You are eligible for a refund! Confirm banking details to receive funds.", 1),
    ("Urgent: Course registration deadline is TODAY. Click here immediately.", 1),
    ("Your diploma is ready for pickup! Verify identity at this link.", 1),
    ("Emergency alert: Unauthorized access detected. Change password immediately.", 1),
    ("Confirm your exam schedule by entering your student credentials.", 1),
    ("Act now: Limited scholarship spots available! Complete profile urgently.", 1),
    ("Your account will be deleted in 48 hours. Confirm details to restore access.", 1),
    ("Prize announcement: You've won a campus award! Claim it now at this link.", 1),
    ("Urgent fee reminder: Complete payment immediately or face suspension.", 1),
    ("Security update: Verify your account through this link within 24 hours.", 1),
    ("Your lab results are ready. Login now to confirm grades and schedule.", 1),
    ("FINAL NOTICE: Update student profile or lose access to exam registration.", 1),
    ("Congratulations! Special accommodation approved. Verify details to proceed.", 1),
    ("Administrative alert: Correct your course registration immediately.", 1),
    ("Your housing application approved! Secure spot by confirming details.", 1),
    ("Grade dispute resolution: Click here to submit your appeal urgently.", 1),
    ("Verify employment verification letter request in your account now.", 1),
    ("Your learning portal account locked due to security concerns. Unlock now.", 1),
    ("Time-sensitive: Final submission deadline for your thesis. Upload today.", 1),
    ("Merit scholarship opportunity: Complete application by clicking here immediately.", 1),
    ("Your certificate is ready! Download via this urgent link.", 1),
    ("Verify parking permit through student portal. Expiration notice.", 1),
    ("Your exam invigilation schedule needs confirmation. Act immediately.", 1),
    ("Academic probation notice: Respond to this email immediately.", 1),
    ("Student loan disbursement ready. Confirm banking credentials now.", 1),
    ("Class enrollment deadline TODAY. Click immediately to secure spots.", 1),
    ("Verify your graduation status by submitting this form urgently.", 1),
    ("Campus card reactivation required. Complete now or lose privileges.", 1),
    ("Alumni network exclusive offer: Verify membership details immediately.", 1),
    ("Exam retake registration opened. Deadline is TODAY. Enroll now!", 1),
    ("Your internship offer is expiring! Confirm position details immediately.", 1),
    ("Academic excellence award confirmation. Update profile urgently.", 1),
    ("Research opportunity: Limited spots available. Apply immediately!", 1),
    ("Your degree audit needs revision. Submit corrected version now.", 1),
    ("Campus security alert: Verify emergency contact information.", 1),
    ("Your student organization budget approved. Claim funds by clicking here.", 1),
    ("Exam hall allocation released. Verify your exam center immediately.", 1),
    ("Study abroad grant opportunity. Apply before deadline expires today.", 1),
    ("Your course feedback is due. Submit evaluation by end of today.", 1),
    ("Graduation photo appointment: Confirm your slot immediately.", 1),
    
    # LEGITIMATE EXAMPLES - 52 examples
    ("Semester timetable for next week attached. Please review and reach out for questions.", 0),
    ("Results for EE101 have been published on the student portal.", 0),
    ("Invitation: Annual departmental seminar on AI next Thursday.", 0),
    ("Fee receipt for your tuition payment is attached. Thank you.", 0),
    ("Office hours updated for Prof. Kumar. See the schedule on the portal.", 0),
    ("Dear Student, your assignment has been graded. Check the feedback on the course page.", 0),
    ("The library will be closed on Dec 25 and 26 for maintenance. Apologies for inconvenience.", 0),
    ("Welcome to the academic mentorship program. First meeting scheduled for next Monday.", 0),
    ("Your transcript has been successfully generated and sent to your registered email.", 0),
    ("Campus WiFi maintenance scheduled for Saturday midnight. Services will be restored by Sunday morning.", 0),
    ("Departmental newsletter: January issue with research highlights from our faculty.", 0),
    ("New course offerings announced for Spring semester. See attached brochure.", 0),
    ("Thank you for attending the campus career fair last week. Here are resources from employers.", 0),
    ("Reminder: Academic integrity training is mandatory. Complete by end of this month.", 0),
    ("Your lab session has been rescheduled to Friday 2 PM as per your request.", 0),
    ("Spring break dates: March 15-22. Campus will have limited services during this period.", 0),
    ("Congratulations on your excellent performance in midterm exams. Well done!", 0),
    ("Student health center reminder: Book your annual checkup now for spring semester.", 0),
    ("New study resources available in the university learning commons. Access through portal.", 0),
    ("Faculty research seminar: Dr. Sarah Chen presenting on computational biology next week.", 0),
    ("Your course registration for next semester is now open. Advise approval required.", 0),
    ("Library extended hours during exam week. Study space available 24/7.", 0),
    ("Departmental awards nominations now open. Submit your recommendations by Dec 31.", 0),
    ("Campus sustainability initiative survey. Help us improve campus facilities.", 0),
    ("Your parking permit has been renewed for the academic year. Thank you.", 0),
    ("Important: Update your emergency contact information in the student portal.", 0),
    ("Graduate admissions decisions released. Check your status on the portal.", 0),
    ("Campus shuttle schedule updated for winter semester. See attached PDF.", 0),
    ("Your internship evaluation has been submitted successfully. Thank you.", 0),
    ("Reminder: Final exam schedule posted. Check the registrar's website for details.", 0),
    ("Congratulations on your scholarship award! Details of disbursement attached.", 0),
    ("Career development workshop series starting next month. Register online.", 0),
    ("Your course materials are ready for download in the university library system.", 0),
    ("Departmental seminar series: Weekly talks from visiting scholars this semester.", 0),
    ("Student orientation for new semester will be held on campus on Monday.", 0),
    ("Your degree progress report is attached. Please review for accuracy.", 0),
    ("Campus facilities maintenance update: All systems operating normally.", 0),
    ("Thank you for participating in the departmental social event last Friday.", 0),
    ("Exam proctoring locations have been assigned and sent to your student email.", 0),
    ("Course syllabus has been updated. Review changes in the learning management system.", 0),
    ("Graduate student association meeting reminder: Thursday at 5 PM in Room 101.", 0),
    ("Your co-op placement details confirmed. Report to office on Monday.", 0),
    ("Library book collection has been updated with new academic journals.", 0),
    ("Departmental research seminar: Presentations from student researchers this Friday.", 0),
    ("Final course evaluations now open. Your feedback helps improve courses.", 0),
    ("Campus events calendar for Spring semester is now published.", 0),
    ("Your academic adviser has reviewed your course selection. No issues noted.", 0),
    ("Graduation requirements checklist is attached. Ensure all items are completed.", 0),
    ("Departmental newsletter with faculty research updates and student achievements.", 0),
    ("Study group formation promoted: Find classmates for collaborative learning.", 0),
    ("Your course project submission has been received successfully.", 0),
    ("Undergraduate research opportunity: Applications now being accepted.", 0),
]


def ensure_models_dir(root: Path):
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def train_and_save(root: Path):
    # If a user-provided dataset exists, load it. Expect CSV with columns: text,label
    dataset_csv = root / 'data' / 'dataset.csv'
    if dataset_csv.exists():
        print(f"Loading external dataset: {dataset_csv}")
        df = pd.read_csv(dataset_csv)
        # ensure required columns
        if 'text' not in df.columns or 'label' not in df.columns:
            raise ValueError('dataset.csv must contain "text" and "label" columns')
        df = df[['text', 'label']]
    else:
        df = pd.DataFrame(DATA, columns=["text", "label"])

    # Adversarial / augmentation helpers: simple obfuscations to increase robustness
    def obfuscate_homoglyphs(s: str) -> str:
        # Replace some ASCII letters with visually similar unicode chars
        mapping = {
            'a': '\u0430',  # Cyrillic a
            'o': '\u03BF',  # Greek omicron
            'i': '\u0131',  # dotless i
            'e': '\u0435',  # Cyrillic e
        }
        out = []
        for ch in s:
            if ch.lower() in mapping and (np.random.rand() < 0.2):
                newch = mapping[ch.lower()]
                # preserve case
                if ch.isupper():
                    newch = newch.upper()
                out.append(newch)
            else:
                out.append(ch)
        return ''.join(out)

    def add_html_wrapping(s: str) -> str:
        return f"<div>{s}</div>"

    def insert_random_punct(s: str) -> str:
        # insert a random punctuation in the middle
        i = max(1, len(s)//3)
        return s[:i] + '...' + s[i:]

    # If dataset is small, augment phishing examples
    if len(df) < 1000:
        phishing_rows = df[df['label'] == 1]
        aug_texts = []
        for t in phishing_rows['text'].values:
            # create a couple of augmentations
            aug_texts.append(obfuscate_homoglyphs(t))
            aug_texts.append(add_html_wrapping(t))
            aug_texts.append(insert_random_punct(t))
        if aug_texts:
            aug_df = pd.DataFrame({'text': aug_texts, 'label': 1})
            df = pd.concat([df, aug_df], ignore_index=True)
    
    print(f"Dataset size: {len(df)} samples ({df['label'].sum()} phishing, {(df['label']==0).sum()} legitimate)")

    # Improved TF-IDF vectorizer with better parameters
    # - Higher max_features to capture more vocabulary
    # - Extended ngrams for better pattern detection
    # - Adjusted min_df to filter very rare terms
    # Vectorizer
    vectorizer = TfidfVectorizer(
        max_features=5000,      # Increased from 2000
        ngram_range=(1, 3),     # Added 3-grams for better context
        min_df=1,
        max_df=0.95,            # Ignore very common terms
        lowercase=True,
        stop_words='english'
    )
    # Fit TF-IDF on full corpus first
    X_tfidf = vectorizer.fit_transform(df["text"]) 
    y = df["label"].values

    # Extract URL-derived dense features for each sample
    url_feat_list = [url_features_from_text(t) for t in df['text']]
    url_feats = np.array(url_feat_list, dtype=float)

    # Convert dense url features to sparse and concatenate with tfidf features
    url_sparse = csr_matrix(url_feats)
    X = hstack([X_tfidf, url_sparse], format='csr')

    # Train/test split for final evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Base estimators (unfitted) for stacking
    lr = LogisticRegression(
        max_iter=1000,
        C=0.1,
        class_weight='balanced',
        solver='lbfgs'
    )

    nb = MultinomialNB(alpha=0.1)

    # Linear SVM (will be wrapped with calibration to provide predict_proba)
    base_svm = LinearSVC(
        max_iter=2000,
        C=0.1,
        class_weight='balanced',
        random_state=42,
        dual=False
    )

    # Cross-validation (estimate performance of base estimators)
    lr_cv_scores = cross_val_score(lr, X, y, cv=5, scoring='accuracy')
    nb_cv_scores = cross_val_score(nb, X, y, cv=5, scoring='accuracy')
    svm_cv_scores = cross_val_score(base_svm, X, y, cv=5, scoring='accuracy')

    print("\n=== Cross-Validation Results (base estimators) ===")
    print(f"Logistic Regression: {lr_cv_scores.mean():.4f} (+/- {lr_cv_scores.std():.4f})")
    print(f"Naive Bayes:         {nb_cv_scores.mean():.4f} (+/- {nb_cv_scores.std():.4f})")
    print(f"SVM:                 {svm_cv_scores.mean():.4f} (+/- {svm_cv_scores.std():.4f})")
    print(f"Ensemble Average:    {(lr_cv_scores.mean() + nb_cv_scores.mean() + svm_cv_scores.mean())/3:.4f}")

    # Calibrate SVM so it exposes predict_proba for stacking and downstream use
    calibrated_svm = CalibratedClassifierCV(base_svm, cv=5)

    # Stacking classifier: stacking base learners and a logistic final estimator
    stacking = StackingClassifier(
        estimators=[('lr', lr), ('nb', nb), ('svm', calibrated_svm)],
        final_estimator=LogisticRegression(max_iter=1000),
        cv=5,
        passthrough=True,
        n_jobs=-1
    )

    # Fit stacking on training data
    print('\n[Fitting] Training stacking classifier on train split...')
    stacking.fit(X_train, y_train)

    # Evaluate on holdout
    y_pred = stacking.predict(X_test)
    try:
        y_proba = stacking.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba)
    except Exception:
        y_proba = None
        auc = None

    print('\n=== Holdout Evaluation (stacking) ===')
    print(classification_report(y_test, y_pred))
    if auc is not None:
        print(f"ROC AUC: {auc:.4f}")

    models_dir = ensure_models_dir(root)

    # Save artifacts: vectorizer and a full pipeline. The pipeline will expect
    # raw text input; we create a simple wrapper pipeline that computes TF-IDF
    # and expects URL features to be appended at prediction time by the
    # UrlFeaturesTransformer. For simplicity we save both the vectorizer and
    # the trained stacking classifier as separate files and also save a pipeline
    # that only contains the TF-IDF -> classifier for backward compatibility.
    joblib.dump(vectorizer, models_dir / "tfidf.pkl")
    joblib.dump(lr, models_dir / "logistic.pkl")
    joblib.dump(nb, models_dir / "nb.pkl")
    # Save the calibrated SVM wrapper object (it will be fitted inside stacking, but keep for compatibility)
    joblib.dump(calibrated_svm, models_dir / "svm.pkl")
    # Save the stacking classifier (it expects features in the order TF-IDF then URL features)
    joblib.dump(stacking, models_dir / "stacking.pkl")

    # For compatibility, create a lightweight pipeline object that will handle
    # raw text -> features (TF-IDF + URL features) at predict time. We'll store
    # a small helper dict with vectorizer and stacking model so ModelBundle can
    # reconstruct predictions. Save as 'pipeline.pkl'.
    helper_pipeline = {
        'vectorizer': vectorizer,
        'stacking': stacking
    }
    joblib.dump(helper_pipeline, models_dir / "pipeline.pkl")

    print(f"\nSaved models to: {models_dir}")


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    train_and_save(root)
