"""Ingest the raw CSV into DuckDB and clean it with SQL."""
from pathlib import Path

import duckdb
import pandas as pd

from .config import SQL_DIR


def _read_raw(csv_path: str | Path) -> pd.DataFrame:
    """Read the raw export.

    The DataCo file is Windows-1252 encoded (curly quotes, accented city names),
    which DuckDB's strict latin-1 reader rejects, so pandas does the decoding.
    """
    return pd.read_csv(csv_path, encoding="cp1252", encoding_errors="replace", low_memory=False)


def _connect_with_orders(csv_path: str | Path, db_path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(db_path)
    raw = _read_raw(csv_path)
    con.register("raw_df", raw)
    con.execute("CREATE OR REPLACE TABLE raw_orders AS SELECT * FROM raw_df")
    con.unregister("raw_df")
    con.execute((SQL_DIR / "clean_orders.sql").read_text())
    return con


def load_orders(csv_path: str | Path, db_path: str = ":memory:") -> pd.DataFrame:
    """Load the raw DataCo CSV, run the SQL cleaning step and return clean orders."""
    con = _connect_with_orders(csv_path, db_path)
    try:
        return con.execute("SELECT * FROM orders").df()
    finally:
        con.close()


def late_rate_report(csv_path: str | Path) -> pd.DataFrame:
    """Late-delivery rate by shipping mode and market."""
    con = _connect_with_orders(csv_path)
    try:
        return con.execute((SQL_DIR / "late_rate_by_segment.sql").read_text()).df()
    finally:
        con.close()
