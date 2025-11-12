import sys
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'src'


def test_train_and_predict():
    # Run training script
    ret = subprocess.run([sys.executable, str(SRC / 'train_models.py')], check=False)
    assert ret.returncode == 0, 'Training script failed'

    # Now try to import predictor and run a sample prediction
    sys.path.insert(0, str(ROOT))
    from app.core.predictor import ModelBundle, predict_phishing

    bundle = ModelBundle(ROOT)
    sample = "Your scholarship verification deadline is tomorrow. Click to verify account now."
    out = predict_phishing(sample, bundle)
    assert 'classification' in out and 'confidence' in out
    assert 0.0 <= out['confidence'] <= 1.0
