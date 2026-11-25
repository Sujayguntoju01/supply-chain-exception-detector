from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
DEFAULT_MODEL_DIR = ROOT / "models"

CATEGORICAL = [
    "payment_type",
    "shipping_mode",
    "market",
    "order_region",
    "customer_segment",
    "category_name",
]
NUMERIC = [
    "days_scheduled",
    "quantity",
    "unit_price",
    "discount_rate",
    "profit_ratio",
    "sales",
    "order_month",
    "order_dow",
    "order_hour",
]
# Financial signals used by the unsupervised order-exception detector.
EXCEPTION_FEATURES = ["quantity", "unit_price", "discount_rate", "profit_ratio", "sales"]
TARGET = "is_late"
