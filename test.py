import requests

BASE_URL = "http://127.0.0.1:8000"


def print_table(headers, rows):
    if not rows:
        print("No data found.")
        return

    col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

    print()
    print(" | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))))
    print("-+-".join("-" * col_widths[i] for i in range(len(headers))))

    for row in rows:
        print(" | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row))))
    print()


def print_order(order):
    headers = ["ID", "Student", "Document", "Pages", "Type", "Cost", "Date"]
    rows = [[
        order["order_id"],
        order["student_name"],
        order["document_name"],
        order["pages"],
        order["print_type"],
        order["total_cost"],
        order["created_at"]
    ]]
    print_table(headers, rows)


def create_order():
    student = input("Student name: ")
    doc = input("Document: ")
    pages = int(input("Pages: "))
    ptype = input("Type (bw/colored/photo): ")

    res = requests.post(f"{BASE_URL}/orders", json={
        "student_name": student,
        "document_name": doc,
        "pages": pages,
        "print_type": ptype
    })

    if res.status_code not in (200, 201):
        print("Error:", res.json())
        return

    print("\n Created:")
    print_order(res.json())


def list_orders():
    res = requests.get(f"{BASE_URL}/orders")
    data = res.json()

    headers = ["ID", "Student", "Document", "Pages", "Type", "Cost", "Date"]
    rows = [[
        o["order_id"],
        o["student_name"],
        o["document_name"],
        o["pages"],
        o["print_type"],
        o["total_cost"],
        o["created_at"]
    ] for o in data]

    print_table(headers, rows)


def get_order():
    order_id = input("Enter Order ID: ")

    res = requests.get(f"{BASE_URL}/orders/{order_id}")

    if res.status_code != 200:
        print("Error:", res.json())
        return

    print("\n Order Details:")
    print_order(res.json())

def view_stats():
    res = requests.get(f"{BASE_URL}/statistics")
    data = res.json()

    print("\n=== STATISTICS ===")
    print(f"Total Orders : {data['total_orders']}")
    print(f"Total Revenue: {data['total_revenue']}")

    # By print type
    print("\n--- By Print Type ---")
    headers = ["Type", "Orders", "Revenue"]
    rows = [[k, v["order_count"], v["total_revenue"]] for k, v in data["by_print_type"].items()]
    print_table(headers, rows)

    # Today
    print("\n--- Today ---")
    print_table(
        ["Date", "Orders", "Revenue"],
        [[data["today"]["date"], data["today"]["order_count"], data["today"]["total_revenue"]]]
    )

    # Last 7 days
    print("\n--- Last 7 Days ---")
    rows = [[d["date"], d["order_count"], d["total_revenue"]] for d in data["last_7_days"]]
    print_table(["Date", "Orders", "Revenue"], rows)


def main():
    while True:
        print("\n=== PRINTSU CLI ===")
        print("1. Create Order")
        print("2. List Orders")
        print("3. Get Order by ID")
        print("4. View Statistics")
        print("0. Exit")

        c = input("Choice: ")

        if c == "1":
            create_order()
        elif c == "2":
            list_orders()
        elif c == "3":
            get_order()
        elif c == "4":
            view_stats()
        elif c == "0":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()