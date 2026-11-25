"""Generate a small synthetic dataset with the same columns as the DataCo export.

The real dataset is ~180K rows and lives on Kaggle; this sample lets the tests,
CI pipeline and Docker build run without downloading it. Do not report metrics
from this file: it is synthetic.

Usage: python scripts/make_sample_data.py --rows 3000 --out data/sample_orders.csv
"""
import argparse
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SHIPPING = {  # mode: (scheduled days, probability of being late)
    "Standard Class": (4, 0.38),
    "Second Class": (2, 0.77),
    "First Class": (1, 0.95),
    "Same Day": (0, 0.46),
}
MARKETS = {
    "LATAM": ["Central America", "South America", "Caribbean"],
    "Europe": ["Western Europe", "Northern Europe", "Southern Europe"],
    "Pacific Asia": ["Southeast Asia", "Eastern Asia", "Oceania"],
    "USCA": ["US Center", "West of USA", "East of USA"],
    "Africa": ["West Africa", "North Africa", "East Africa"],
}
CATEGORIES = {"Cleats": 59.99, "Men's Footwear": 129.99, "Women's Apparel": 50.0,
              "Indoor/Outdoor Games": 49.98, "Fishing": 399.98, "Water Sports": 199.99}


def make(rows: int, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    modes = rng.choice(list(SHIPPING), rows, p=[0.6, 0.2, 0.15, 0.05])
    markets = rng.choice(list(MARKETS), rows)
    cats = rng.choice(list(CATEGORIES), rows)
    start = datetime(2015, 1, 1)
    records = []
    for i in range(rows):
        sched, p_late = SHIPPING[modes[i]]
        late = rng.random() < p_late
        real = sched + (rng.integers(1, 4) if late else -rng.integers(0, min(sched, 2) + 1))
        qty = int(rng.integers(1, 6))
        price = CATEGORIES[cats[i]]
        disc = float(rng.choice([0.0, 0.04, 0.1, 0.15, 0.25]))
        ratio = float(rng.normal(0.12, 0.25))
        if rng.random() < 0.02:  # injected order exceptions
            disc, ratio, qty = 0.9, float(rng.uniform(-2.5, -1.5)), int(rng.integers(20, 40))
        sales = round(price * qty, 2)
        total = sales * (1 - disc)
        ts = start + timedelta(minutes=int(rng.integers(0, 3 * 365 * 24 * 60)))
        records.append({
            "Type": rng.choice(["DEBIT", "TRANSFER", "CASH", "PAYMENT"]),
            "Days for shipping (real)": max(int(real), 0),
            "Days for shipment (scheduled)": sched,
            "Benefit per order": round(total * ratio, 2),
            "Sales per customer": round(total, 2),
            "Delivery Status": "Late delivery" if late else "Shipping on time",
            "Late_delivery_risk": int(late),
            "Category Name": cats[i],
            "Customer Segment": rng.choice(["Consumer", "Corporate", "Home Office"]),
            "Department Name": "Fan Shop",
            "Market": markets[i],
            "Order Id": 100000 + i // 2,
            "Order Item Id": i + 1,
            "order date (DateOrders)": f"{ts.month}/{ts.day}/{ts.year} {ts.hour}:{ts.minute:02d}",
            "Order Item Discount Rate": disc,
            "Order Item Product Price": price,
            "Order Item Profit Ratio": round(ratio, 2),
            "Order Item Quantity": qty,
            "Sales": sales,
            "Order Item Total": round(total, 2),
            "Order Profit Per Order": round(total * ratio, 2),
            "Order Region": rng.choice(MARKETS[markets[i]]),
            "Order Status": rng.choice(["COMPLETE", "PENDING", "PROCESSING", "CLOSED", "CANCELED"],
                                       p=[0.4, 0.2, 0.2, 0.17, 0.03]),
            "Shipping Mode": modes[i],
        })
    return pd.DataFrame(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=3000)
    parser.add_argument("--out", default="data/sample_orders.csv")
    args = parser.parse_args()
    make(args.rows).to_csv(args.out, index=False, encoding="latin-1")
    print(f"Wrote {args.rows} synthetic rows to {args.out}")
