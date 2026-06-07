# 🗃️ SQL + Power BI — Retail Sales Analysis

An end-to-end analyst workflow: a **relational SQLite database** queried with **SQL**
(JOINs + aggregations) feeding an interactive **Power BI** dashboard. Built on a
40-customer / 13-product / 800-order store database.

## 🔄 The pipeline
```
store.db (3 tables)  ->  SQL queries (JOIN + GROUP BY)  ->  powerbi_sales.csv  ->  Power BI dashboard
```

## 🔑 What the SQL reveals
- **₹25.2M** total revenue across **800 orders** (avg **₹31,483** per order)
- **Technology drives ~70% of revenue** (₹17.6M) — Furniture ₹7.0M, Office Supplies ₹0.5M
- **Consumer** is the top segment (₹10.3M), ahead of Corporate (₹8.8M) and Small Business (₹6.1M)
- Top customer — Customer 030 (Bengaluru) — spent **₹1.34M**

## 🧱 Database schema
- **customers** (customer_id, customer_name, city, segment)
- **products** (product_id, product_name, category, unit_price)
- **orders** (order_id, order_date, customer_id → customers, product_id → products, quantity)
- Revenue is computed by JOIN: `quantity × unit_price`

## 📁 Files
| File | What it is |
|---|---|
| `build_database.py` | Creates `data/store.db` (Python standard library only) |
| `sql/queries.sql` | 6 business questions answered in SQL (JOINs, GROUP BY) |
| `export_for_powerbi.py` | Joins the tables → `data/powerbi_sales.csv` for Power BI |
| `BUILD_GUIDE.md` | Step-by-step: run the SQL, then build the dashboard |
| `Sales_Analysis.pbix` | The Power BI dashboard *(you add this after building)* |

## 🛠️ Skills demonstrated
SQL (JOIN, GROUP BY, aggregate functions) · relational data modeling · SQLite ·
Power BI · DAX · building an analyst data pipeline
