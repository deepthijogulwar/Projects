"""Create a small relational SQLite database (data/store.db) for the project.

Three tables — customers, products, orders — so you can practise real SQL JOINs.
Run once:  python build_database.py   (uses only the Python standard library)
"""
import os
import random
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "store.db")

random.seed(42)

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune"]
SEGMENTS = ["Consumer", "Corporate", "Small Business"]
PRODUCTS = [
    ("Laptop", "Technology", 55000),
    ("Smartphone", "Technology", 30000),
    ("Monitor", "Technology", 12000),
    ("Headphones", "Technology", 2500),
    ("Office Chair", "Furniture", 8000),
    ("Desk", "Furniture", 15000),
    ("Bookshelf", "Furniture", 6000),
    ("Filing Cabinet", "Furniture", 9000),
    ("Whiteboard", "Office Supplies", 2000),
    ("Stapler", "Office Supplies", 250),
    ("Printer Paper", "Office Supplies", 300),
    ("Pen Set", "Office Supplies", 150),
    ("Notebook", "Office Supplies", 80),
]


def main():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)

    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE customers (
            customer_id   INTEGER PRIMARY KEY,
            customer_name TEXT,
            city          TEXT,
            segment       TEXT
        );
        CREATE TABLE products (
            product_id   INTEGER PRIMARY KEY,
            product_name TEXT,
            category     TEXT,
            unit_price   INTEGER
        );
        CREATE TABLE orders (
            order_id    INTEGER PRIMARY KEY,
            order_date  TEXT,
            customer_id INTEGER,
            product_id  INTEGER,
            quantity    INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
            FOREIGN KEY (product_id)  REFERENCES products (product_id)
        );
        """
    )

    customers = [(i, f"Customer {i:03d}", random.choice(CITIES), random.choice(SEGMENTS))
                 for i in range(1, 41)]
    cur.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)

    products = [(i + 1, name, cat, price) for i, (name, cat, price) in enumerate(PRODUCTS)]
    cur.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)

    orders = []
    for order_id in range(1, 801):
        order_date = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        customer_id = random.randint(1, 40)
        product_id = random.randint(1, len(PRODUCTS))
        quantity = random.randint(1, 5)
        orders.append((order_id, order_date, customer_id, product_id, quantity))
    cur.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)

    con.commit()

    revenue = cur.execute(
        "SELECT SUM(o.quantity * p.unit_price) "
        "FROM orders o JOIN products p ON o.product_id = p.product_id"
    ).fetchone()[0]
    print(f"Built {DB}")
    print(f"  customers={len(customers)}  products={len(products)}  orders={len(orders)}")
    print(f"  total revenue (computed via JOIN) = {revenue}")
    con.close()


if __name__ == "__main__":
    main()
