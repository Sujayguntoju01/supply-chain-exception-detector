import json


def test_training_writes_models_and_metrics(trained_model_dir):
    assert (trained_model_dir / "late_model.joblib").exists()
    assert (trained_model_dir / "exception_model.joblib").exists()
    metrics = json.loads((trained_model_dir / "metrics.json").read_text())
    assert 0 <= metrics["late_model"]["precision"] <= 1
    assert metrics["late_model"]["roc_auc"] > 0.6  # shipping mode is a strong signal
    assert metrics["exception_model"]["flagged_rows"] > 0
