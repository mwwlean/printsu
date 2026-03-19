from fastapi import FastAPI, HTTPException
from db import init_db
from models import Order, OrderCreate
import services

app = FastAPI(title="Printsu")


@app.on_event("startup")
def startup():
    init_db()


@app.post("/orders", response_model=Order)
def create_order(payload: OrderCreate):
    if payload.pages <= 0:
        raise HTTPException(status_code=422, detail="Invalid pages")

    try:
        return services.create_order(payload)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.get("/orders", response_model=list[Order])
def list_orders():
    return services.list_orders()


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    row = services.get_order(order_id)
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return row


@app.get("/statistics")
def statistics():
    return services.get_statistics()