from datetime import date, timedelta
from config import PRICE_PER_PAGE
from db import read_all, insert_row, next_id, find_by_id


def calculate_cost(pages, print_type):
    rate = PRICE_PER_PAGE.get(print_type)
    if not rate:
        raise ValueError("Invalid print type")
    return round(pages * rate, 2)


def create_order(data):
    cost = calculate_cost(data.pages, data.print_type)

    row = {
        "order_id": next_id(),
        "student_name": data.student_name,
        "document_name": data.document_name,
        "pages": data.pages,
        "print_type": data.print_type,
        "total_cost": cost,
        "created_at": date.today().isoformat(),
    }

    insert_row(row)
    return row


def list_orders():
    return read_all()


def get_order(order_id):
    return find_by_id(order_id)

def get_statistics():
    rows = read_all()

    total_orders = len(rows)
    total_revenue = round(sum(float(r["total_cost"]) for r in rows), 2)

    by_type = {}
    for r in rows:
        pt = r["print_type"]
        by_type.setdefault(pt, {"order_count": 0, "total_revenue": 0})
        by_type[pt]["order_count"] += 1
        by_type[pt]["total_revenue"] += float(r["total_cost"])

    def daily_stat(d):
        d_str = d.isoformat()
        day_rows = [r for r in rows if r["created_at"] == d_str]
        return {
            "date": d_str,
            "order_count": len(day_rows),
            "total_revenue": round(sum(float(r["total_cost"]) for r in day_rows), 2),
        }

    today = date.today()
    last_7_days = [daily_stat(today - timedelta(days=i)) for i in range(6, -1, -1)]

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "by_print_type": by_type,
        "today": daily_stat(today),
        "last_7_days": last_7_days,
    }