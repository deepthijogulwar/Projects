"""
build_notebook.py
=================
Assembles and EXECUTES the showcase notebook so it ships with all tables and
charts already rendered:

    notebooks/01_sales_analysis.ipynb

Run:  python build_notebook.py
"""
from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat.v4 import new_code_cell as code
from nbformat.v4 import new_markdown_cell as md
from nbformat.v4 import new_notebook

ROOT = Path(__file__).parent
NB_DIR = ROOT / "notebooks"
NB_DIR.mkdir(exist_ok=True)

cells = [
    md("# 📊 Sales & Revenue Intelligence — Analysis Notebook\n"
       "\n"
       "An end-to-end analysis of the real **Sample - Superstore** dataset that goes "
       "beyond pretty charts. For each limitation of a typical sales dashboard, this "
       "notebook shows the **fix**:\n"
       "\n"
       "| # | Limitation of the typical dashboard | The fix shown below |\n"
       "|---|---|---|\n"
       "| 3 | Breaks on messy data | Auditable cleaning pipeline |\n"
       "| 2 | Vanity metric: total sales | Profit & margin → loss-making bestsellers |\n"
       "| 1a | Only backward-looking | Back-tested forecast (model selection) |\n"
       "| 1b | Silent on sudden changes | Automatic anomaly detection |\n"
       "| 1c | Ends at a chart | Quantified recommendations |"),

    md("## 0 · Setup"),
    code("import sys, warnings\n"
         "from pathlib import Path\n"
         "warnings.filterwarnings('ignore')\n"
         "sys.path.insert(0, str(Path.cwd()))\n"
         "import pandas as pd\n"
         "from IPython.display import Image, display\n"
         "from src import pipeline\n"
         "from src.superstore_loader import ensure_dataset\n"
         "pipeline.CURRENCY = '$'        # this is US data\n"
         "pd.set_option('display.max_columns', 30)\n"
         "print('Setup complete · Python', sys.version.split()[0])"),

    md("## 1 · Load the real Superstore data\n"
       "Auto-downloads on first run. This public mirror is *deliberately messy* — "
       "perfect for showing the cleaning step on genuinely real data."),
    code("csv = ensure_dataset('data/superstore.csv')\n"
         "raw = pd.read_csv(csv)\n"
         "print('Raw shape:', raw.shape)\n"
         "raw.head()"),

    md("### Real data is messy\n"
       "Before trusting any total, look at the data quality. A naive "
       "`read_csv().sum()` would silently include hundreds of blank rows."),
    code("print('Fully-blank order dates :', raw['Order Date'].isna().sum())\n"
         "print('Exact duplicate rows     :', raw.duplicated().sum())\n"
         "raw.isna().sum().to_frame('nulls').query('nulls > 0')"),

    md("## 2 · Clean the data — **FIX #3**\n"
       "The cleaner parses dates, drops blank/duplicate rows, normalises text and "
       "validates numbers — and **logs every fix** so the work is auditable."),
    code("df, report = pipeline.clean_data(csv)\n"
         "pd.Series(report, name='value').to_frame()"),
    md("> ✅ Loaded 10,800 rows → kept the canonical **9,994** real transactions "
       "(92.5%), having removed **806 blank junk rows**."),

    md("## 3 · Profitability — **FIX #2** (the headline)\n"
       "Revenue is a vanity metric. **Profit and margin** tell the truth."),
    code("prof = pipeline.profitability_analysis(df)\n"
         "print(f\"Sales ${prof['total_sales']:,.0f}  |  \"\n"
         "      f\"Profit ${prof['total_profit']:,.0f}  |  \"\n"
         "      f\"Margin {prof['overall_margin_pct']:.1f}%\")\n"
         "prof['by_category']"),
    md("### 🚨 Loss-making bestsellers\n"
       "High-revenue sub-categories that **lose money** — the insight a "
       "'top products' chart completely hides:"),
    code("prof['loss_makers']"),
    md("> **Tables** and **Bookcases** sell well but lose **\\$17,725** and "
       "**\\$3,473** to deep discounting. This is the most famous real insight in "
       "this dataset."),

    md("## 4 · Forecast — **FIX #1a** (back-tested model selection)\n"
       "Instead of reporting flattering *in-sample* error, we **hold out the last "
       "6 months**, forecast them blind, and compare three models by true "
       "*out-of-sample* accuracy."),
    code("fc = pipeline.forecast_sales(df, periods=6)\n"
         "print('Chosen model :', fc['model_name'])\n"
         "print(f\"OOS MAPE      : {fc['oos_mape']:.1f}%\")\n"
         "print(f\"Next 6 months : ${fc['next_total']:,.0f}\")\n"
         "fc['comparison']"),

    md("## 5 · Anomaly detection — **FIX #1b**\n"
       "Flag any day outside a rolling mean ± 3σ band — automatic, objective "
       "monitoring instead of eyeballing a line chart."),
    code("anom = pipeline.detect_anomalies(df)\n"
         "print('Anomaly days flagged:', len(anom['anomalies']))\n"
         "anom['anomalies'].tail(5).to_frame('sales')"),

    md("## 6 · Recommendations — **FIX #1c**\n"
       "Numbers are useless without an action. The pipeline turns the analysis "
       "into quantified business recommendations."),
    code("for i, r in enumerate(pipeline.generate_recommendations(prof, fc, anom), 1):\n"
         "    print(f'{i}. {r}\\n')"),

    md("## 7 · The executive dashboard\n"
       "All four views in one image (also saved to `outputs/`)."),
    code("pipeline.save_all_charts(prof, fc, anom, 'outputs')\n"
         "display(Image('outputs/dashboard.png'))"),
    code("for img in ['loss_making_products.png', 'discount_vs_profit.png',\n"
         "            'sales_forecast.png', 'anomaly_detection.png']:\n"
         "    display(Image(f'outputs/{img}'))"),

    md("## ✅ Conclusion\n"
       "This isn't a chart-making exercise — it's an analyst workflow: **clean** "
       "messy real data, **question** the vanity metrics, **predict** the future "
       "with back-tested rigour, **monitor** for anomalies, and **recommend** "
       "concrete actions.\n"
       "\n"
       "**Limitations & next steps:** the forecast is univariate (a SARIMAX with "
       "promotions/holidays as drivers would improve it); anomaly detection is "
       "statistical, not causal. See the [README](../README.md) for the full write-up."),
]

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
})

print("Executing notebook (this runs the whole analysis)...")
ExecutePreprocessor(timeout=600, kernel_name="python3").preprocess(
    nb, {"metadata": {"path": str(ROOT)}})

out = NB_DIR / "01_sales_analysis.ipynb"
nbf.write(nb, out)
print("Wrote executed notebook ->", out)
