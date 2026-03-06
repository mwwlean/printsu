import csv
import os
from datetime import date
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------

PRICE_PER_PAGE = {
    "bw": 3.00,
    "colored": 10.00,
    "photo": 20.00,
}


def calculate_cost(pages: int, print_type: str) -> float:
    rate = PRICE_PER_PAGE.get(print_type)
    if rate is None:
        raise ValueError(f"Unknown print_type '{print_type}'. Valid options: {list(PRICE_PER_PAGE)}")
    return round(pages * rate, 2)


# ---------------------------------------------------------------------------
# CSV Database
# ---------------------------------------------------------------------------

DB_FILE = "printsu.csv"

# Table columns — order matters (mirrors SQL column order)
COLUMNS = ["order_id", "student_name", "document_name", "pages", "print_type", "total_cost", "created_at"]


def init_db():
    """Create the CSV file with headers if it does not exist."""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()


def read_all() -> list[dict]:
    """Return all rows as a list of dicts."""
    with open(DB_FILE, "r", newline="") as f:
        return list(csv.DictReader(f))


def next_id() -> int:
    """Auto-increment: max existing order_id + 1."""
    rows = read_all()
    if not rows:
        return 1
    return max(int(r["order_id"]) for r in rows) + 1


def insert_row(row: dict):
    """Append a new row to the CSV."""
    with open(DB_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writerow(row)


def find_by_id(order_id: int) -> Optional[dict]:
    """Return the row matching order_id, or None."""
    for row in read_all():
        if int(row["order_id"]) == order_id:
            return row
    return None


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Order(BaseModel):
    order_id: int
    student_name: str
    document_name: str
    pages: int
    print_type: str          # "bw" | "colored" | "photo"
    total_cost: float
    created_at: Optional[str] = None


class OrderCreate(BaseModel):
    student_name: str
    document_name: str
    pages: int
    print_type: str


class PrintTypeStat(BaseModel):
    order_count: int
    total_revenue: float


class DailyStat(BaseModel):
    date: str
    order_count: int
    total_revenue: float


class StatsResponse(BaseModel):
    total_orders: int
    total_revenue: float
    by_print_type: dict[str, PrintTypeStat]
    today: DailyStat
    last_7_days: list[DailyStat]


def row_to_order(row: dict) -> Order:
    return Order(
        order_id=int(row["order_id"]),
        student_name=row["student_name"],
        document_name=row["document_name"],
        pages=int(row["pages"]),
        print_type=row["print_type"],
        total_cost=float(row["total_cost"]),
        created_at=row.get("created_at") or None,
    )


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Printsu", description="Campus Printing Management System")


@app.on_event("startup")
def on_startup():
    init_db()


# POST /orders — create a new order
@app.post("/orders", response_model=Order, status_code=201)
def create_order(payload: OrderCreate):
    if payload.pages <= 0:
        raise HTTPException(status_code=422, detail="pages must be a positive integer")

    try:
        cost = calculate_cost(payload.pages, payload.print_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    row = {
        "order_id": next_id(),
        "student_name": payload.student_name,
        "document_name": payload.document_name,
        "pages": payload.pages,
        "print_type": payload.print_type,
        "total_cost": cost,
        "created_at": date.today().isoformat(),
    }
    insert_row(row)
    return row_to_order(row)


# GET /orders — list all orders
@app.get("/orders", response_model=list[Order])
def list_orders():
    return [row_to_order(r) for r in read_all()]


# GET /orders/{id} — retrieve a single order
@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    row = find_by_id(order_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return row_to_order(row)


# ---------------------------------------------------------------------------
# Statistics  (Shop Owner)
# ---------------------------------------------------------------------------

@app.get("/statistics", response_model=StatsResponse)
def get_statistics():
    """Aggregate business stats: totals, per-print-type breakdown, and daily view."""
    rows = read_all()

    total_orders = len(rows)
    total_revenue = round(sum(float(r["total_cost"]) for r in rows), 2)

    # --- breakdown by print type ---
    by_type: dict[str, dict] = {}
    for r in rows:
        pt = r["print_type"]
        if pt not in by_type:
            by_type[pt] = {"order_count": 0, "total_revenue": 0.0}
        by_type[pt]["order_count"] += 1
        by_type[pt]["total_revenue"] = round(by_type[pt]["total_revenue"] + float(r["total_cost"]), 2)

    by_print_type = {k: PrintTypeStat(**v) for k, v in by_type.items()}

    # --- daily helpers ---
    from datetime import timedelta

    def daily_stat(target: date) -> DailyStat:
        target_str = target.isoformat()
        day_rows = [r for r in rows if r.get("created_at") == target_str]
        return DailyStat(
            date=target_str,
            order_count=len(day_rows),
            total_revenue=round(sum(float(r["total_cost"]) for r in day_rows), 2),
        )

    today = date.today()
    last_7 = [daily_stat(today - timedelta(days=i)) for i in range(6, -1, -1)]

    return StatsResponse(
        total_orders=total_orders,
        total_revenue=total_revenue,
        by_print_type=by_print_type,
        today=daily_stat(today),
        last_7_days=last_7,
    )
