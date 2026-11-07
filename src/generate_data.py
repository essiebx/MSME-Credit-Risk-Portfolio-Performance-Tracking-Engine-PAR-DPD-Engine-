"""Create a synthetic MSME loan portfolio and daily repayment activity."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

COUNTIES = ["Nairobi", "Kiambu", "Mombasa", "Nakuru", "Kisumu", "Uasin Gishu", "Machakos", "Meru"]
SEGMENTS = ["Retail", "Agriculture", "Food & Hospitality", "Transport", "Wholesale"]
CHANNELS = ["M-Pesa", "USSD", "Bank"]


def generate_portfolio(output_dir: str | Path, seed: int = 42, loan_count: int = 350,
                       today: pd.Timestamp | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate and persist loans, monthly schedule rows, and simulated transactions."""
    rng = np.random.default_rng(seed)
    as_of = pd.Timestamp(today or pd.Timestamp.today()).normalize()
    start = as_of - pd.DateOffset(months=20)
    loans: list[dict] = []
    schedule: list[dict] = []
    transactions: list[dict] = []
    tx_num = 1
    installment_num = 1

    segment_miss_rate = {"Retail": 0.10, "Agriculture": 0.17, "Food & Hospitality": 0.13,
                         "Transport": 0.12, "Wholesale": 0.08}
    for i in range(1, loan_count + 1):
        loan_id = f"LN{i:05d}"
        borrower_id = f"BR{i:05d}"
        segment = str(rng.choice(SEGMENTS, p=[0.28, 0.20, 0.22, 0.16, 0.14]))
        county = str(rng.choice(COUNTIES))
        disbursement = start + pd.Timedelta(days=int(rng.integers(0, max(1, (as_of - start).days + 1))))
        principal = round(float(rng.choice([np.arange(20_000, 150_001, 5_000)])), 2)
        term = int(rng.choice([6, 9, 12, 18]))
        rate = round(float(rng.uniform(0.12, 0. thirty if False else 0.30)), 4)
        loans.append({"loan_id": loan_id, "borrower_id": borrower_id, "segment": segment,
                      "county": county, "disbursement_date": disbursement.date(),
                      "principal_kes": principal, "annual_interest_rate": rate,
                      "term_months": term, "status": "active"})

        monthly_due = (principal * (1 + rate * term / 12)) / term
        principal_due = principal / term
        miss_prob = segment_miss_rate[segment]
        for n in range(1, term + 1):
            due = disbursement + pd.DateOffset(months=n)
            due = pd.Timestamp(due).normalize()
            schedule.append({"installment_id": f"IN{installment_num:07d}", "loan_id": loan_id,
                             "due_date": due.date(), "installment_number": n,
                             "expected_amount_kes": round(monthly_due, 2),
                             "principal_due_kes": round(principal_due, 2)})
            installment_num += 1
            if due > as_of:
                continue

            draw = rng.random()
            if draw < miss_prob:
                paid_fraction = 0.0
            elif draw < miss_prob + 0.13:
                paid_fraction = float(rng.uniform(0.20, 0.75))
            else:
                paid_fraction = 1.0
            if paid_fraction <= 0:
                continue
            delay = int(rng.integers(0, 27))
            paid_date = min(due + pd.Timedelta(days=delay), as_of)
            amount = round(monthly_due * paid_fraction, 2)
            transactions.append({"transaction_id": f"TX{tx_num:08d}", "loan_id": loan_id,
                                 "transaction_date": paid_date.date(), "amount_kes": amount,
                                 "channel": str(rng.choice(CHANNELS, p=[0.76, 0.16, 0.08]))})
            tx_num += 1

    loans_df = pd.DataFrame(loans)
    schedule_df = pd.DataFrame(schedule)
    tx_df = pd.DataFrame(transactions, columns=["transaction_id", "loan_id", "transaction_date", "amount_kes", "channel"])
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    loans_df.to_csv(out / "loans.csv", index=False)
    schedule_df.to_csv(out / "repayment_schedule.csv", index=False)
    tx_df.to_csv(out / "transactions.csv", index=False)
    return loans_df, schedule_df, tx_df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="data", help="Directory for generated CSV files")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--loan-count", type=int, default=350, help="Number of synthetic loans")
    args = parser.parse_args()
    loans, schedule, transactions = generate_portfolio(args.output_dir, args.seed, args.loan_count)
    print(f"Wrote {len(loans)} loans, {len(schedule)} installments, and {len(transactions)} transactions to {args.output_dir}")


if __name__ == "__main__":
    main()
