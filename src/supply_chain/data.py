"""Ingest the raw CSV into DuckDB and clean it with SQL."""
from pathlib import Path

import duckdb
import pandas as pd

from .config import SQL_DIR


def load_orders(csv_path: str | Path, db_path: str = ":memory:") -> pd.DataFrame:
    """Load the raw DataCo CSV, run the SQL cleaning step and return clean orders."""
    con = duckdb.connect(db_path)
    try:
        con.execute(
            "CREATE OR REPLACE TABLE raw_orders AS "
            "SELECT * FROM read_csv(?, header = true, encoding = 'latin-1', sample_size = -1)",
            [str(csv_path)],
        )
        con.execute((SQL_DIR / "clean_orders.sql").read_text())
        return con.execute("SELECT * FROM orders").df()
    finally:
        con.close()


def late_rate_report(csv_path: str | Path) -> pd.DataFrame:
    """Late-delivery rate by shipping mode and market."""
    con = duckdb.connect()
    try:
        con.execute(
            "CREATE TABLE raw_orders AS "
            "SELECT * FROM read_csv(?, header = true, encoding = 'latin-1', sample_size = -1)",
            [str(csv_path)],
        )
        con.execute((SQL_DIR / "clean_orders.sql").read_text())
        return con.execute((SQL_DIR / "late_rate_by_segment.sql").read_text()).df()
    finally:
        con.close()
