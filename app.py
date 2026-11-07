"""Interactive synthetic MSME credit portfolio dashboard."""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics import loan_snapshot, monthly_metrics
from src.generate_data import generate_portfolio

st.set_page_config(page_title="MSME Portfolio Health", page_icon="📊", layout="wide")
st.title("MSME Credit Portfolio Health")
st.caption("Synthetic Kenyan MSME portfolio | DPD, PAR, collections, and disbursements")

DATA_DIR = Path(__file__).parent / "data"
FILES = [DATA_DIR / "loans.csv", DATA_DIR / "repayment_schedule.csv", DATA_DIR / "transactions.csv"]
if not all(path.exists() for path in FILES):
    with st.spinner("Creating synthetic demo portfolio…"):
        generate_portfolio(DATA_DIR)

@st.cache_data
def load_data():
    loans = pd.read_csv(FILES[0], parse_dates=["disbursement_date"])
    schedule = pd.read_csv(FILES[1], parse_dates=["due_date"])
    tx = pd.read_csv(FILES[2], parse_dates=["transaction_date"])
    return loans, schedule, tx

loans, schedule, transactions = load_data()
latest_date = min(pd.Timestamp.today().normalize(), schedule["due_date"].max())
first_date = pd.to_datetime(loans["disbursement_date"]).min()
with st.sidebar:
    st.header("Report filters")
    picked_date = st.date_input("Portfolio as-of date", value=latest_date.date(),
                                 min_value=first_date.date(), max_value=latest_date.date())
    segments = sorted(loans["segment"].dropna().unique().tolist())
    selected_segments = st.multiselect("Merchant segments", segments, default=segments)

snapshot = loan_snapshot(loans, schedule, transactions, pd.Timestamp(picked_date))
snapshot = snapshot[snapshot["segment"].isin(selected_segments)]
monthly = monthly_metrics(loans[loans["segment"].isin(selected_segments)],
                          schedule[schedule["loan_id"].isin(loans[loans["segment"].isin(selected_segments)]["loan_id"])],
                          transactions[transactions["loan_id"].isin(loans[loans["segment"].isin(selected_segments)]["loan_id"])])

balance = snapshot["outstanding_principal_kes"].sum()
loan_count = snapshot["loan_id"].nunique()
if balance > 0:
    par = {n: snapshot.loc[snapshot["dpd"] >= n, "outstanding_principal_kes"].sum() / balance for n in (30, 60, 90)}
else:
    par = {30: 0.0, 60: 0.0, 90: 0.0}

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Outstanding principal", f"KES {balance:,.0f}")
c2.metric("Loans in portfolio", f"{loan_count:,}")
c3.metric("PAR 30", f"{par[30]:.1%}")
c4.metric("PAR 60", f"{par[60]:.1%}")
c5.metric("PAR 90", f"{par[90]:.1%}")

st.subheader("Monthly portfolio activity")
if not monthly.empty:
    activity = monthly.melt(id_vars="month", value_vars=["disbursements_kes", "expected_collections_kes", "actual_collections_kes"],
                            var_name="metric", value_name="KES")
    fig = px.line(activity, x="month", y="KES", color="metric", markers=True,
                  labels={"month": "Month", "KES": "KES", "metric": "Metric"})
    st.plotly_chart(fig, use_container_width=True)
    rate_fig = px.line(monthly, x="month", y="collection_rate", markers=True,
                       labels={"month": "Month", "collection_rate": "Actual / expected collections"})
    rate_fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(rate_fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("DPD aging")
    bucket = pd.cut(snapshot["dpd"], bins=[-1, 0, 29, 59, 89, float("inf")],
                    labels=["Current", "1–29", "30–59", "60–89", "90+"])
    aging = snapshot.assign(dpd_bucket=bucket).groupby("dpd_bucket", observed=False)["outstanding_principal_kes"].sum().reset_index()
    st.plotly_chart(px.bar(aging, x="dpd_bucket", y="outstanding_principal_kes",
                           labels={"dpd_bucket": "DPD bucket", "outstanding_principal_kes": "Outstanding principal (KES)"}),
                    use_container_width=True)
with right:
    st.subheader("90+ DPD loan rate by segment")
    if not snapshot.empty:
        segment_risk = snapshot.groupby("segment").agg(
            loans=("loan_id", "nunique"), loans_90_plus=("dpd", lambda values: int((values >= 90).sum()))).reset_index()
        segment_risk["loan_rate_90_plus"] = segment_risk["loans_90_plus"] / segment_risk["loans"].clip(lower=1)
        fig = px.bar(segment_risk, x="segment", y="loan_rate_90_plus", color="segment",
                     labels={"segment": "Merchant segment", "loan_rate_90_plus": "Loans at 90+ DPD"})
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No loans match the selected filters.")

st.caption("Synthetic data only. Collection rate compares received cash in each month with scheduled installments due in that month.")
