# Supply Chain Exception Detector

[![CI](https://github.com/Sujayguntoju01/supply-chain-exception-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/Sujayguntoju01/supply-chain-exception-detector/actions/workflows/ci.yml)

An end-to-end ML pipeline that flags **order items likely to ship late** and **orders with unusual economics** (extreme discounts, negative margins, abnormal basket sizes) in the [DataCo Smart Supply Chain dataset](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) (~180K order items). The models are served as a Dockerized **FastAPI** service, deployed to **AWS EC2** with model artifacts in **S3**, and tested and shipped through **GitHub Actions CI/CD**.

## Architecture

```
 DataCo CSV ──► DuckDB + SQL cleaning ──► feature engineering ──► models ──► S3
 (Kaggle)       sql/clean_orders.sql      time + categorical       │
                                                                   ▼
             GitHub Actions: lint → tests → Docker build → deploy ──► EC2: FastAPI in Docker
                                                                      /predict  /predict/batch
```

| Stage | What happens | Code |
|---|---|---|
| Ingest | Raw CSV (latin-1) loaded into DuckDB | `src/supply_chain/data.py` |
| Clean | SQL renames columns, parses timestamps, drops cancelled orders, de-duplicates order items | `sql/clean_orders.sql` |
| Features | Order month, weekday and hour; one-hot shipping mode, market, region, segment and category | `src/supply_chain/features.py` |
| Late-delivery model | `HistGradientBoostingClassifier` using only order-time features (no leakage from actual shipping days) | `src/supply_chain/train.py` |
| Exception detector | `IsolationForest` over quantity, price, discount rate, profit ratio and sales; flags the most unusual 2% | `src/supply_chain/train.py` |
| Serve | FastAPI with validated request schema; loads models from disk or S3 | `api/main.py` |
| CI/CD | Ruff + pytest + Docker build + container smoke test; SSH deploy to EC2 | `.github/workflows/` |

## Results

Results on the full DataCo dataset (20% stratified hold-out), from `models/metrics.json` after `make train`:

| Metric | Value |
|---|---|
| Order items | _run `make train`_ |
| Late-delivery precision | _…_ |
| Late-delivery recall | _…_ |
| ROC AUC | _…_ |
| Orders flagged as exceptions | _…_ |

## Quick start

```bash
git clone https://github.com/Sujayguntoju01/supply-chain-exception-detector.git
cd supply-chain-exception-detector
make install

# Option A: real data (needs a Kaggle API token in ~/.kaggle/kaggle.json)
make data && make train

# Option B: synthetic sample (no download, for trying it out)
make sample
PYTHONPATH=src python -m supply_chain.train --data data/sample_orders.csv

make serve          # http://localhost:8000/docs
```

Example request:

```bash
curl -X POST localhost:8000/predict -H 'content-type: application/json' -d '{
  "order_ts": "2018-01-31T22:56:00", "shipping_mode": "First Class", "days_scheduled": 1,
  "market": "LATAM", "order_region": "Central America", "customer_segment": "Consumer",
  "category_name": "Cleats", "quantity": 1, "unit_price": 59.99,
  "discount_rate": 0.04, "profit_ratio": 0.29, "sales": 59.99 }'
```

```json
{"late_probability": 0.96, "late_risk": true, "exception_score": 0.46, "is_exception": false}
```

## Run with Docker

```bash
make train          # creates models/*.joblib
docker build -t supply-chain-exception-detector .
docker run -p 8000:8000 supply-chain-exception-detector
```

## Deploy to AWS

1. **S3:** upload trained models
   `PYTHONPATH=src python -m supply_chain.train --data data/DataCoSupplyChainDataset.csv --s3-uri s3://<bucket>/supply-chain/`
2. **EC2:** launch an Amazon Linux / Ubuntu instance with Docker installed, an IAM role that can read the bucket, and port 80 open. Clone this repo into `~/supply-chain-exception-detector`.
3. **GitHub:** add the secrets `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` and `MODEL_S3_URI`, and the repository variable `DEPLOY_ENABLED=true`.

Every push to `main` that passes CI then rebuilds and restarts the container on EC2.

## Tests

```bash
make lint test
```

Tests run on a synthetic dataset with the same schema (`scripts/make_sample_data.py`), so CI never needs the Kaggle download. They cover the SQL cleaning step, model training, API validation, and checking that an injected abnormal order gets flagged.

## Project structure

```
├── api/main.py                 FastAPI app
├── sql/                        DuckDB cleaning + reporting queries
├── src/supply_chain/           data, features, train, predict
├── scripts/                    Kaggle download, synthetic sample generator
├── tests/                      pytest suite
├── Dockerfile
└── .github/workflows/          CI and EC2 deploy
```

## Tech

Python · SQL (DuckDB) · pandas · scikit-learn · FastAPI · Docker · AWS EC2 & S3 · GitHub Actions
