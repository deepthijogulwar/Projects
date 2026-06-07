# 🛠️ Build Guide — SQL + Power BI Sales Analysis

Two parts: **(A)** run SQL against a real database, then **(B)** build a Power BI
dashboard on the exported data. ~40 minutes total.

---

## Part A — SQL (the database)

### A0 · Tools
- The database is created by a Python script — **Python 3 only, no installs**.
- To run SQL visually, install **DB Browser for SQLite** (free): sqlitebrowser.org.
  *(Alternatives: the `sqlite3` command line, or the VS Code SQLite extension.)*

### A1 · Build the database
```powershell
python build_database.py
```
Creates `data/store.db` with three tables: **customers** (40), **products** (13), **orders** (800).

### A2 · Run the queries
Open `data/store.db` in DB Browser → **Execute SQL** tab → paste a query from
`sql/queries.sql` → run. The six queries cover **JOINs, GROUP BY, aggregates, and sorting**.
Expected results:

| Query | What you should see |
|---|---|
| 1 · Headline KPIs | 800 orders · **₹25,186,090** revenue · ₹31,483 avg order |
| 2 · Revenue by category | Technology **₹17.6M (~70%)** > Furniture ₹7.0M > Office Supplies ₹0.53M |
| 3 · Top customer | Customer 030 (Bengaluru) — ₹1,335,850 |
| 4 · Revenue by segment | Consumer ₹10.3M > Corporate ₹8.8M > Small Business ₹6.1M |
| 6 · Best-seller (units) | Filing Cabinet — 226 units |

That's the **SQL skill** — JOINs and aggregation on a relational database.

---

## Part B — Power BI (the dashboard)

### B1 · Export the data
```powershell
python export_for_powerbi.py
```
Runs a three-table JOIN and writes `data/powerbi_sales.csv` (800 rows — one per order,
with customer, product, and a computed `revenue` column).

### B2 · Build the dashboard
1. Install **Power BI Desktop** (free, Microsoft Store) → open it.
2. **Home → Get data → Text/CSV** → load `data/powerbi_sales.csv`.
3. **Home → New measure** — paste each:
```DAX
Total Revenue = SUM(powerbi_sales[revenue])
Total Orders = COUNTROWS(powerbi_sales)
Avg Order Value = DIVIDE([Total Revenue], [Total Orders])
```
4. Build the visuals:
   - **KPI cards:** Total Revenue (≈ ₹25.2M), Total Orders (800), Avg Order Value (≈ ₹31.5K)
   - **Bar chart:** `category` vs Total Revenue → Technology dominates
   - **Column chart:** `segment` vs Total Revenue
   - **Line chart:** `order_date` (set to Month) vs Total Revenue
   - **Bar chart:** `customer_name` vs Total Revenue, with a **Top 5** filter
   - **Bar/Map:** `city` vs Total Revenue
5. Add **slicers**: `category`, `segment`, `city`.
6. **File → Save as** `Sales_Analysis.pbix`, and save a `dashboard.png` screenshot here.

✅ Done — you've gone from a **SQL database → Power BI dashboard**, the exact pipeline
analyst jobs ask for. You can now back up **SQL**, **Power BI**, and **DAX** on your resume.
