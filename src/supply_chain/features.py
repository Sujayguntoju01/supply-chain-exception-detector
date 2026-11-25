"""Feature engineering shared by training and inference."""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from .config import CATEGORICAL, NUMERIC


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ts = pd.to_datetime(out["order_ts"])
    out["order_month"] = ts.dt.month
    out["order_dow"] = ts.dt.dayofweek
    out["order_hour"] = ts.dt.hour
    return out


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            (
                "cat",
                OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20, sparse_output=False),
                CATEGORICAL,
            ),
            ("num", "passthrough", NUMERIC),
        ]
    )
