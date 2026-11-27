# MSME Credit Risk Portfolio Performance Tracking

## Project at a glance

**What problem did you solve?**  
Track the health of a micro, small, and medium enterprise (MSME) loan portfolio by measuring delinquency, portfolio-at-risk (PAR), outstanding principal, collections, and disbursements across time and merchant segments.

**What data and tools did you use?**  
The project uses a reproducible, seeded synthetic Kenyan MSME portfolio: loan records, daily installment schedules, and simulated M-Pesa, USSD, and bank transactions. The implementation uses Python, pandas, Streamlit, Plotly, and DuckDB, with reusable SQL in `sql/`.

**What did you find or build?**  
Built an interactive portfolio dashboard and supporting analytics that calculate loan-level days past due (DPD), FIFO payment allocation, estimated outstanding principal, PAR 30/60/90, monthly disbursement and collection trends, collection rates, DPD aging buckets, and segment-level 90+ DPD loan rates. It also includes a data dictionary and SQL analytics queries. This is an analytics demonstration, not a validated credit-risk model or portfolio result.

**How can someone run or view it?**  
Run it locally with the Quick start commands below. Open `app.py` through Streamlit with `streamlit run app.py`. There is currently no published live dashboard or committed screenshot. Add the deployed dashboard URL and dashboard screenshots here when they are available.

> **Synthetic data notice:** All borrower, loan, and transaction records are synthetic and do not represent real customers or real portfolio performance. The metrics are for demonstration only and must not be used as lending, investment, or credit decisions.

> **Unfinished/work-in-progress:** This project is not production-ready. The generator uses simplified repayment behavior and a fixed scheduled principal assumption rather than full loan amortization or accounting rules. It has not been validated against real lender data and does not include model governance, privacy controls, or production data integrations.

## Features

- Seeded synthetic portfolio for Kenyan merchant segments and counties.
- Daily installment schedules and simulated M-Pesa, USSD, and bank collection transactions.
- FIFO payment allocation to installments for loan-level DPD and outstanding balance estimates.
- PAR 30/60/90, monthly disbursements, due-versus-collected cash, collection rate, and segment-level 90+ DPD rates.
- Reusable DuckDB SQL schema and analytics queries alongside the Python dashboard.
- A data dictionary describing fields, units, and metric definitions.

## Quick start

Requires Python 3.10 or later.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src.generate_data --output-dir data
streamlit run app.py
```

The generator writes `loans.csv`, `repayment_schedule.csv`, and `transactions.csv` into `data/`. The dashboard generates those files on first launch if they do not exist. You can regenerate the portfolio with a different seed by using `python -m src.generate_data --output-dir data --seed 42`.

## Dashboard

Use the as-of date selector to view the portfolio snapshot and choose one or more merchant segments. The dashboard includes:

- Outstanding principal and loan count.
- PAR 30, PAR 60, and PAR 90 by outstanding principal exposure.
- Monthly disbursement and collection trends.
- Due-versus-actual collections and collection rate.
- DPD aging buckets and segment-level 90+ DPD loan rates.

PAR denominator is the total estimated outstanding principal for loans disbursed by the selected as-of date. A loan enters a PAR cohort when its DPD is at least the threshold; its outstanding principal is then included in that PAR cohort.

## Project layout

```text
.
├── app.py
├── data/                       # Generated CSVs (not committed)
├── DATA_DICTIONARY.md
├── requirements.txt
├── sql/
│   ├── 01_schema.sql
│   ├── 02_loan_dpd.sql
│   └── 03_monthly_portfolio.sql
└── src/
    ├── __init__.py
    ├── analytics.py
    └── generate_data.py
```

## SQL usage

The SQL targets DuckDB. Create the tables using `sql/01_schema.sql`, then load the generated CSVs into the corresponding tables. For example, in the DuckDB CLI:

```sql
.read sql/01_schema.sql
INSERT INTO loans SELECT * FROM read_csv_auto('data/loans.csv', header=true);
INSERT INTO repayment_schedule SELECT * FROM read_csv_auto('data/repayment_schedule.csv', header=true);
INSERT INTO transactions SELECT * FROM read_csv_auto('data/transactions.csv', header=true);
```

Set the `as_of_date` CTE value in `sql/02_loan_dpd.sql` to the desired snapshot date. `sql/03_monthly_portfolio.sql` reports expected installments by due month, transactions by receipt month, and disbursements by month.

## Metric notes and assumptions

- Installments use a fixed scheduled amount and a flat scheduled principal component; this is a synthetic analytical assumption, not an amortization or accounting model.
- Collections are attributed to the month cash is received, while expected collections are attributed to the installment due month. Therefore monthly collection rate compares period cash receipts to period scheduled installments.
- Payments are allocated oldest installment first. Excess payments can reduce future scheduled principal exposure.
- PAR is measured on estimated outstanding principal, not the original disbursed amount or overdue installment value.
- The generator models simulated repayment behavior only; it is not intended to represent real Kenyan borrowers or payment behavior.

## Reproducibility

```bash
python -m src.generate_data --output-dir data --seed 42
```

The same seed and generation date produce the same dataset. Do not use real personal or financial data in this demo without implementing appropriate access controls, privacy safeguards, and governance.
