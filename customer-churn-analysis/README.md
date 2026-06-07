# 📉 Telco Customer Churn Analysis

**One in four customers is leaving — costing ~$1.67M (≈ ₹13.9 crore) a year.**
This project finds *who* is leaving, *what* they have in common, and *how much* it costs —
then recommends concrete, prioritized actions to keep them. It is a **business analysis**,
not a prediction model.

## 🔑 Key findings
- **Overall churn rate: 26.5%** (1,869 of 7,043 customers).
- **Contract is the #1 factor:** month-to-month churns **42.7%** vs **2.8%** on two-year contracts.
- **The first year is the danger zone:** 0–12 month customers churn ~**47%**.
- **Electronic check** users churn **~45%** vs **~15–17%** for auto-pay users.
- **Fiber optic** customers churn **~42%** — more than double DSL.

## 🎯 Highest-risk segment
Month-to-month + fiber optic + electronic check → **60.4% churn across 1,307 customers** —
more than double the company average.

## ✅ Recommendations
1. Convert month-to-month customers to 1–2 year contracts (biggest lever).
2. Launch a first-90-days onboarding program.
3. Nudge electronic-check users toward auto-pay.
4. Audit fiber pricing & service quality.
5. Bundle tech support / online security into plans.

## ⚠️ Limitations
- **Correlation ≠ causation** — these are *associated* factors, not proven causes.
- **Imbalanced data** (~26.5% churners), so the focus is business insight, not model accuracy.
- **Single snapshot** in time; no competitor or complaint data.

## ▶️ How to run it
1. Download the dataset (see `data/HOW_TO_GET_THE_DATA.txt`) and put the CSV in `data/`.
2. In PowerShell, from this project folder:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   jupyter notebook
   ```
3. Open `notebooks/churn_analysis.ipynb` and run the cells top to bottom.
   Charts are saved into `outputs/`.

## 🛠️ Tech used
Python · pandas · numpy · matplotlib · seaborn · scikit-learn · Jupyter

## 📁 Structure
```
customer-churn-analysis/
├── data/        raw dataset (you download the CSV here)
├── notebooks/   churn_analysis.ipynb  ← the full, narrated analysis
├── outputs/     charts saved as .png when you run the notebook
├── README.md
├── requirements.txt
└── .gitignore
```
