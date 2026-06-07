# 🤖 Auto-Analyst — Automated Insights Report Generator

> Point it at a sales CSV and **one command turns it into a full written report** —
> KPIs, charts, anomaly + loss-maker detection, and a plain-English executive
> summary. Schedule it and the report **regenerates itself** every week. It
> automates the busywork an analyst does by hand.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![pandas](https://img.shields.io/badge/pandas-data-150458)
![automation](https://img.shields.io/badge/runs-on%20a%20schedule-success)
![AI summary](https://img.shields.io/badge/exec%20summary-AI%20optional-orange)

## What it does
```
$ python run_report.py
Report written to: outputs/report.md
Charts written:    ['trend.png', 'sales_by_category.png', 'profit_by_category.png']

--- Executive summary ---
Across 24 months (Jan 2024-Dec 2025), total sales were $... at a ...% profit margin.
... Furniture is loss-making (-$...). Nov 2025 stands out as an outlier ...
```
Output: a ready-to-share **[outputs/report.md](outputs/report.md)** with charts embedded.

## Why this stands out
Most analytics portfolio projects are a **one-off notebook** someone has to open and
re-run by hand. This is a **reusable tool that runs itself**:

| One-off notebook | This project |
|---|---|
| Manual: open, run cells, copy charts | **One command** → finished report |
| Only the author can reproduce it | Runs on **any CSV**, for anyone |
| Forgotten until someone asks | **Scheduled** — regenerates every Monday |
| Just charts | Charts **+ a written summary + flagged risks** (loss-makers, anomalies) |

## How it works
```
sales.csv
   |  metrics.py    -> KPIs, monthly trend, top segments, loss-makers, anomalies
   |  charts.py     -> trend / sales-by-category / profit-by-category  (PNG)
   |  narrative.py  -> executive summary  (LLM if a key is set, else a template)
   v  report.py     -> assemble -> outputs/report.md
```

## Quickstart
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python generate_sample_data.py   # creates the demo dataset (run once)
python run_report.py             # -> outputs/report.md + charts
```

## Automate it (the point of the project)
Make the report regenerate itself every Monday at 8 AM:
```powershell
powershell -ExecutionPolicy Bypass -File .\schedule_weekly.ps1
```
That registers a Windows Scheduled Task. (On macOS/Linux, add a `cron` line:
`0 8 * * 1 cd /path && python run_report.py`.)

## Use your own data
```powershell
python run_report.py --data path\to\your_sales.csv --out reports
```
Works on any CSV with `date`, `region`, `category`, `sales`, and `profit` columns.

## AI-written summary (optional)
By default the executive summary is a clear **template** filled with the real numbers
(runs free, offline). Add an API key for an LLM-written version:
```powershell
pip install openai
$env:OPENAI_API_KEY = "sk-..."     # or $env:GITHUB_TOKEN for free GitHub Models
python run_report.py
```
The LLM only **rephrases verified numbers** — it is not asked to invent figures.

## ⚠️ Limitations (read honestly)
- **Demo data is synthetic** (seeded generator) so results are reproducible; the
  loss-making category and the anomalous month are baked in to show detection works.
- **Anomaly detection is a simple z-score** — good for a flag, not a forecast.
- **Assumes a tidy CSV** with the expected columns; messy real data may need mapping.
- **The AI summary needs a key**; without one you get the (still accurate) template.

## Tech stack
Python · pandas · NumPy · Matplotlib · Windows Task Scheduler / cron ·
*(optional)* OpenAI-compatible LLM (OpenAI / Azure / free GitHub Models)

## Roadmap
- Config file for column mapping (any schema)
- HTML / PDF export and email delivery
- Period-over-period comparisons baked into the charts
- Forecasting + confidence bands
