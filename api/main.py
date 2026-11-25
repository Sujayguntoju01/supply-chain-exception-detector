"""FastAPI service that scores orders for late-delivery risk and order exceptions."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

from supply_chain.predict import load_models, score


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    load_models()  # fail fast if models are missing
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Supply Chain Exception Detector",
    description="Flags order items likely to ship late and orders with unusual economics.",
    version="1.0.0",
)


class Order(BaseModel):
    order_ts: datetime = Field(examples=["2018-01-31T22:56:00"])
    payment_type: Literal["DEBIT", "TRANSFER", "CASH", "PAYMENT"] = "DEBIT"
    shipping_mode: Literal["Standard Class", "Second Class", "First Class", "Same Day"]
    days_scheduled: int = Field(ge=0, le=10, examples=[4])
    market: str = Field(examples=["LATAM"])
    order_region: str = Field(examples=["Central America"])
    customer_segment: str = Field(examples=["Consumer"])
    category_name: str = Field(examples=["Cleats"])
    quantity: int = Field(gt=0, examples=[1])
    unit_price: float = Field(ge=0, examples=[59.99])
    discount_rate: float = Field(ge=0, le=1, examples=[0.04])
    profit_ratio: float = Field(examples=[0.29])
    sales: float = Field(ge=0, examples=[59.99])


class Prediction(BaseModel):
    late_probability: float
    late_risk: bool
    exception_score: float
    is_exception: bool


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
def predict(order: Order) -> Prediction:
    return Prediction(**score([order.model_dump()])[0])


@app.post("/predict/batch", response_model=list[Prediction])
def predict_batch(orders: list[Order]) -> list[Prediction]:
    return [Prediction(**p) for p in score([o.model_dump() for o in orders])]
