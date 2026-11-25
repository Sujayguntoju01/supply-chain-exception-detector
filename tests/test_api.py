import pytest
from fastapi.testclient import TestClient

ORDER = {
    "order_ts": "2018-01-31T22:56:00",
    "payment_type": "DEBIT",
    "shipping_mode": "First Class",
    "days_scheduled": 1,
    "market": "LATAM",
    "order_region": "Central America",
    "customer_segment": "Consumer",
    "category_name": "Cleats",
    "quantity": 1,
    "unit_price": 59.99,
    "discount_rate": 0.04,
    "profit_ratio": 0.29,
    "sales": 59.99,
}


@pytest.fixture()
def client(trained_model_dir, monkeypatch):
    monkeypatch.setenv("MODEL_DIR", str(trained_model_dir))
    from supply_chain.predict import load_models

    load_models.cache_clear()
    from api.main import app

    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_predict(client):
    body = client.post("/predict", json=ORDER).json()
    assert 0 <= body["late_probability"] <= 1
    assert isinstance(body["is_exception"], bool)


def test_unusual_order_is_flagged(client):
    weird = {**ORDER, "quantity": 35, "discount_rate": 0.9, "profit_ratio": -2.2, "sales": 2099.65}
    assert client.post("/predict", json=weird).json()["is_exception"] is True


def test_batch_and_validation(client):
    assert len(client.post("/predict/batch", json=[ORDER, ORDER]).json()) == 2
    assert client.post("/predict", json={**ORDER, "quantity": 0}).status_code == 422
