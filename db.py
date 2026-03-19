import csv
import os

DB_FILE = "printsu.csv"
COLUMNS = [
    "order_id",
    "student_name",
    "document_name",
    "pages",
    "print_type",
    "total_cost",
    "created_at",
]


def init_db():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        with open(DB_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()


def read_all():
    with open(DB_FILE, "r", newline="") as f:
        return list(csv.DictReader(f))


def next_id():
    rows = read_all()
    return max([int(r["order_id"]) for r in rows], default=0) + 1


def find_by_id(order_id):
    for r in read_all():
        if int(r["order_id"]) == order_id:
            return r
    return None


def insert_row(row):
    # 🔥 ensure newline before appending (prevents corruption)
    if os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0:
        with open(DB_FILE, "rb+") as f:
            f.seek(-1, os.SEEK_END)
            if f.read(1) != b"\n":
                f.write(b"\n")

    with open(DB_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writerow(row)