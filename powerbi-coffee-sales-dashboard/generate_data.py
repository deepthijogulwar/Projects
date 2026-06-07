"""Generate a clean, deterministic coffee-shop sales dataset for the Power BI demo.

Run once:  python generate_data.py
Produces:  data/coffee_shop_sales.csv  (one flat table — easiest to model in Power BI)
"""
import csv
import os
import numpy as np

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "coffee_shop_sales.csv")

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Pune"]
PAYMENTS = ["UPI", "Card", "Cash"]
PAYMENT_W = [0.55, 0.30, 0.15]
MENU = {
    "Coffee":      {"Espresso": 120, "Cappuccino": 180, "Latte": 200, "Cold Brew": 220},
    "Tea":         {"Masala Chai": 80, "Green Tea": 100, "Lemon Tea": 90},
    "Bakery":      {"Croissant": 150, "Muffin": 120, "Cookie": 60},
    "Cold Drinks": {"Iced Tea": 140, "Smoothie": 250, "Cola": 90},
    "Snacks":      {"Sandwich": 180, "Samosa": 40, "Fries": 120},
}
CATEGORIES = list(MENU.keys())
CATEGORY_W = [0.40, 0.18, 0.17, 0.13, 0.12]  # a coffee shop sells mostly coffee
N_ROWS = 2000


def main():
    rng = np.random.default_rng(7)
    start = np.datetime64("2025-01-01")
    rows = []
    for _ in range(N_ROWS):
        date = str(start + np.timedelta64(int(rng.integers(0, 365)), "D"))  # YYYY-MM-DD
        city = str(rng.choice(CITIES))
        category = str(rng.choice(CATEGORIES, p=CATEGORY_W))
        product = str(rng.choice(list(MENU[category].keys())))
        unit_price = MENU[category][product]
        quantity = int(rng.integers(1, 4))  # 1-3 items
        sales = quantity * unit_price
        payment = str(rng.choice(PAYMENTS, p=PAYMENT_W))
        rows.append([date, city, category, product, quantity, unit_price, sales, payment])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "City", "Category", "Product", "Quantity", "UnitPrice", "Sales", "PaymentMethod"])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
