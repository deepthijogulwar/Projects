"""Run one SQL JOIN and export a flat table for Power BI.

orders + customers + products  ->  data/powerbi_sales.csv  (one row per order,
with the joined customer/product fields and a computed revenue column).

Run:  python export_for_powerbi.py   (standard library only)
"""
import csv
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "data", "store.db")
OUT = os.path.join(HERE, "data", "powerbi_sales.csv")

QUERY = """
SELECT
    o.order_id,
    o.order_date,
    c.customer_name,
    c.city,
    c.segment,
    p.product_name,
    p.category,
    p.unit_price,
    o.quantity,
    (o.quantity * p.unit_price) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN products  p ON o.product_id  = p.product_id
ORDER BY o.order_date
"""


def main():
    if not os.path.exists(DB):
        raise SystemExit("store.db not found — run  python build_database.py  first.")
    con = sqlite3.connect(DB)
    cur = con.execute(QUERY)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    con.close()

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
