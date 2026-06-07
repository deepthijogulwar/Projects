# 🛠️ Build Guide — Coffee Shop Sales Dashboard (Power BI)

Build this dashboard in ~30 minutes. No prior Power BI experience needed. The data
is one flat table, so there's **no data modeling** to worry about — the easy path.

## Step 0 — Install Power BI Desktop (free, one time)
Microsoft Store → search **"Power BI Desktop"** → Install. *(Windows only; or download free from powerbi.microsoft.com.)*

## Step 1 — Load the data
1. Open Power BI Desktop → **Home → Get data → Text/CSV**.
2. Choose `data/coffee_shop_sales.csv` → **Open** → **Load**.
3. A table named **coffee_shop_sales** appears in the **Data** pane (right).

## Step 2 — Check data types (30 seconds)
Open **Data view** (table icon, left). Confirm:
- `Date` → **Date**  (if it's Text: click the column → *Column tools → Data type → Date*)
- `Quantity`, `UnitPrice`, `Sales` → **Whole number / Decimal**
- `City`, `Category`, `Product`, `PaymentMethod` → **Text**

## Step 3 — Create 4 measures
**Home → New measure**, paste one, press Enter — repeat for all four (also in `DAX_measures.txt`):
```DAX
Total Sales = SUM(coffee_shop_sales[Sales])
Total Transactions = COUNTROWS(coffee_shop_sales)
Total Quantity = SUM(coffee_shop_sales[Quantity])
Avg Transaction Value = DIVIDE([Total Sales], [Total Transactions])
```

## Step 4 — Build the visuals (Report view)
Click a visual icon in the **Visualizations** pane, then drag fields into its wells.

**A) Four KPI cards (top row)** — use the **Card** visual, one measure each. They should read:
| Card | Value |
|---|---|
| Total Sales | **₹551,130** *(may display as 551.13K)* |
| Total Transactions | **2,000** |
| Total Quantity | **3,964** |
| Avg Transaction Value | **₹276** |

**B) Sales trend** — **Line chart**: X-axis = `Date` (set the level to **Month**), Y-axis = `Total Sales`.

**C) Sales by Category** — **Clustered bar chart**: Y-axis = `Category`, X-axis = `Total Sales`.
→ Coffee leads at ~₹278,380.

**D) Sales by City** — **Clustered column chart**: X-axis = `City`, Y-axis = `Total Sales`.
→ Pune tops at ~₹117,760.

**E) Payment mix** — **Donut chart**: Legend = `PaymentMethod`, Values = `Total Sales`.
→ UPI ~56% (~₹306,860).

**F) Top products** — **Bar chart**: Y-axis = `Product`, X-axis = `Total Sales`. In the **Filters** pane, set a **Top N** filter = Top 5 by Total Sales.
→ Latte leads (~₹81,200).

## Step 5 — Add slicers (makes it interactive)
Add three **Slicer** visuals — one each for `City`, `Category`, and `Date`. Now clicking any slicer filters the whole page.

## Step 6 — Make it look good
- Add a **Text box** title: *"Coffee Shop Sales Dashboard — 2025"*.
- **View → Themes** → pick one (e.g., *Executive*).
- Arrange: KPI cards across the top, charts in the middle, slicers down one side.

## Step 7 — Save & show it off
- **File → Save as** → `Coffee_Shop_Sales.pbix` (in this folder).
- **File → Export → PDF**, or use the **Snipping Tool** to save a `dashboard.png` here — that screenshot goes in your README and on your resume/LinkedIn.

✅ Done — an interactive Power BI dashboard with DAX measures, multiple visuals, and slicers. You can now truthfully put **Power BI** and **DAX** on your resume.
