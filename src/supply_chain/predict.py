"""Load trained models and score orders."""
import os
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from .config import CATEGORICAL, DEFAULT_MODEL_DIR, EXCEPTION_FEATURES, NUMERIC
from .features import add_time_features

LATE_THRESHOLD = float(os.getenv("LATE_THRESHOLD", "0.5"))


def _download_from_s3(s3_uri: str, model_dir: Path) -> None:
    import boto3

    bucket, _, prefix = s3_uri.removeprefix("s3://").partition("/")
    model_dir.mkdir(parents=True, exist_ok=True)
    s3 = boto3.client("s3")
    for f in ("late_model.joblib", "exception_model.joblib"):
        s3.download_file(bucket, f"{prefix.rstrip('/')}/{f}".lstrip("/"), str(model_dir / f))


@lru_cache(maxsize=1)
def load_models():
    model_dir = Path(os.getenv("MODEL_DIR", DEFAULT_MODEL_DIR))
    s3_uri = os.getenv("MODEL_S3_URI")
    if s3_uri and not (model_dir / "late_model.joblib").exists():
        _download_from_s3(s3_uri, model_dir)
    return (
        joblib.load(model_dir / "late_model.joblib"),
        joblib.load(model_dir / "exception_model.joblib"),
    )


def score(orders: list[dict]) -> list[dict]:
    late_model, exception_model = load_models()
    df = add_time_features(pd.DataFrame(orders))
    proba = late_model.predict_proba(df[CATEGORICAL + NUMERIC])[:, 1]
    exc_score = -exception_model.score_samples(df[EXCEPTION_FEATURES])
    is_exc = exception_model.predict(df[EXCEPTION_FEATURES]) == -1
    return [
        {
            "late_probability": round(float(p), 4),
            "late_risk": bool(p >= LATE_THRESHOLD),
            "exception_score": round(float(s), 4),
            "is_exception": bool(e),
        }
        for p, s, e in zip(proba, exc_score, is_exc, strict=True)
    ]
