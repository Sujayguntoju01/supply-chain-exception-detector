"""Train the late-delivery classifier and the order-exception detector.

Usage:
    python -m supply_chain.train --data data/DataCoSupplyChainDataset.csv
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, IsolationForest
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .config import CATEGORICAL, DEFAULT_MODEL_DIR, EXCEPTION_FEATURES, NUMERIC, TARGET
from .data import load_orders
from .features import add_time_features, build_preprocessor


def train(csv_path: str | Path, model_dir: str | Path = DEFAULT_MODEL_DIR, seed: int = 42) -> dict:
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    orders = add_time_features(load_orders(csv_path))
    X = orders[CATEGORICAL + NUMERIC]
    y = orders[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=seed
    )

    # 1) Supervised: will this order item be delivered late?
    late_model = Pipeline(
        [
            ("prep", build_preprocessor()),
            ("clf", HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, random_state=seed)),
        ]
    )
    late_model.fit(X_train, y_train)
    proba = late_model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    # 2) Unsupervised: unusual order economics (discounts, margins, basket size).
    exception_model = IsolationForest(n_estimators=200, contamination=0.02, random_state=seed)
    exception_model.fit(orders[EXCEPTION_FEATURES])
    flagged = exception_model.predict(orders[EXCEPTION_FEATURES]) == -1

    metrics = {
        "rows": int(len(orders)),
        "late_rate": round(float(y.mean()), 4),
        "late_model": {
            "precision": round(float(precision_score(y_test, pred)), 4),
            "recall": round(float(recall_score(y_test, pred)), 4),
            "f1": round(float(f1_score(y_test, pred)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, proba)), 4),
            "test_rows": int(len(y_test)),
        },
        "exception_model": {
            "flagged_rows": int(flagged.sum()),
            "flagged_share": round(float(flagged.mean()), 4),
            "median_profit_ratio_flagged": round(float(np.median(orders.loc[flagged, "profit_ratio"])), 4)
            if flagged.any()
            else None,
        },
    }

    joblib.dump(late_model, model_dir / "late_model.joblib")
    joblib.dump(exception_model, model_dir / "exception_model.joblib")
    (model_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def upload_to_s3(model_dir: Path, s3_uri: str) -> None:
    import boto3

    bucket, _, prefix = s3_uri.removeprefix("s3://").partition("/")
    s3 = boto3.client("s3")
    for f in ("late_model.joblib", "exception_model.joblib", "metrics.json"):
        s3.upload_file(str(model_dir / f), bucket, f"{prefix.rstrip('/')}/{f}".lstrip("/"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Path to DataCoSupplyChainDataset.csv")
    parser.add_argument("--model-dir", default=str(DEFAULT_MODEL_DIR))
    parser.add_argument("--s3-uri", help="Optional s3://bucket/prefix to upload trained models to")
    args = parser.parse_args()

    metrics = train(args.data, args.model_dir)
    print(json.dumps(metrics, indent=2))
    if args.s3_uri:
        upload_to_s3(Path(args.model_dir), args.s3_uri)
        print(f"Uploaded models to {args.s3_uri}")


if __name__ == "__main__":
    main()
