from supply_chain.data import late_rate_report, load_orders


def test_sql_cleaning_drops_cancelled_and_renames(sample_csv):
    orders = load_orders(sample_csv)
    assert "CANCELED" not in set(orders["order_status"])
    assert orders["order_item_id"].is_unique
    assert {"shipping_mode", "days_scheduled", "is_late", "order_ts"} <= set(orders.columns)
    assert str(orders["order_ts"].dtype).startswith("datetime64")


def test_late_rate_report(sample_csv):
    report = late_rate_report(sample_csv)
    assert {"shipping_mode", "market", "late_pct"} <= set(report.columns)
    assert report["late_pct"].between(0, 100).all()
