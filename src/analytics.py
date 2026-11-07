"""Portfolio calculations shared by the dashboard and report workflows."""
from __future__ import annotations

import pandas as pd


def loan_snapshot(loans: pd.DataFrame, schedule: pd.DataFrame, transactions: pd.DataFrame,
                  as_of_date: str | pd.Timestamp) -> pd.DataFrame:
    """Return one row per disbursed loan with DPD and estimated principal balance.

    Payments are allocated FIFO against scheduled installments. DPD is based on
    the oldest installment still unpaid as of the requested date.
    """
    as_of = pd.Timestamp(as_of_date).normalize()
    eligible = loans[pd.to_datetime(loans["disbursement_date"]) <= as_of].copy()
    sched = schedule.copy()
    sched["due_date"] = pd.to_datetime(sched["due_date"])
    sched = sched[sched["loan_id"].isin(eligible["loan_id"])].sort_values(
        ["loan_id", "due_date", "installment_number"])
    tx = transactions.copy()
    if not tx.empty:
        tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])
        tx = tx[(tx["transaction_date"] <= as_of) & tx["loan_id"].isin(eligible["loan_id"])]
        paid = tx.groupby("loan_id")["amount_kes"].sum()
    else:
        paid = pd.Series(dtype=float)

    rows = []
    for loan_id, group in sched.groupby("loan_id", sort=False):
        total_paid = float(paid.get(loan_id, 0.0))
        expected = group["expected_amount_kes"].astype(float)
        cumulative_due = expected.cumsum()
        cumulative_before = cumulative_due - expected
        remaining_after = (cumulative_due - total_paid).clip(lower=0)
        remaining_before = (cumulative_before - total_paid).clip(lower=0)
        outstanding_installment = (remaining_after - remaining_before).clip(lower=0)
        overdue = (group["due_date"] <= as_of) & (outstanding_installment > 0.01)
        dpd = int((as_of - group.loc[overdue, "due_date"]).dt.days.max()) if overdue.any() else 0
        principal_balance = (outstanding_installment / expected.replace(0, float("nan"))
                             * group["principal_due_kes"].astype(float)).fillna(0).sum()
        loan = eligible.loc[eligible["loan_id"] == loan_id].iloc[0]
        rows.append({"loan_id": loan_id, "borrower_id": loan["borrower_id"],
                     "segment": loan["segment"], "county": loan["county"],
                     "disbursement_date": pd.Timestamp(loan["disbursement_date"]),
                     "principal_kes": float(loan["principal_kes"]), "dpd": dpd,
                     "outstanding_principal_kes": max(0.0, float(principal_balance))})
    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(columns=["loan_id", "borrower_id", "segment", "county", "disbursement_date",
                                     "principal_kes", "dpd", "outstanding_principal_kes"])
    return result


def monthly_metrics(loans: pd.DataFrame, schedule: pd.DataFrame,
                    transactions: pd.DataFrame) -> pd.DataFrame:
    """Aggregate disbursements, scheduled dues, and cash receipts by calendar month."""
    disb = loans.copy()
    disb["month"] = pd.to_datetime(disb["disbursement_date"]).dt.to_period("M").dt.to_timestamp()
    disbursement = disb.groupby("month").agg(disbursements_kes=("principal_kes", "sum"),
                                              disbursed_loans=("loan_id", "nunique"))
    due = schedule.copy()
    due["month"] = pd.to_datetime(due["due_date"]).dt.to_period("M").dt.to_timestamp()
    expected = due.groupby("month")["expected_amount_kes"].sum().rename("expected_collections_kes")
    actual = transactions.copy()
    if actual.empty:
        collected = pd.Series(dtype=float, name="actual_collections_kes")
    else:
        actual["month"] = pd.to_datetime(actual["transaction_date"]).dt.to_period("M").dt.to_timestamp()
        collected = actual.groupby("month")["amount_kes"].sum().rename("actual_collections_kes")
    out = pd.concat([disbursement, expected, collected], axis=1).fillna(0).sort_index().reset_index()
    out["collection_rate"] = out["actual_collections_kes"].div(
        out["expected_collections_kes"].replace(0, float("nan"))).fillna(0)
    return out
