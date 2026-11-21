import pandas as pd
import pytest

from src.analytics import loan_snapshot, monthly_metrics
from src.generate_data import generate_portfolio


@pytest.fixture
def portfolio(tmp_path):
    return generate_portfolio(tmp_path, seed=42, loan_count=25, today=pd.Timestamp("2026-11-07"))


def test_generator_is_reproducible(tmp_path):
    loans_a, schedule_a, transactions_a = generate_portfolio(tmp_path / "a", seed=42, loan_count=25, today=pd.Timestamp("2026-11-07"))
    loans_b, schedule_b, transactions_b = generate_portfolio(tmp_path / "b", seed=42, loan_count=25, today=pd.Timestamp("2026-11-07"))

    pd.testing.assert_frame_equal(loans_a, loans_b)
    pd.testing.assert_frame_equal(schedule_a, schedule_b)
    pd.testing.assert_frame_equal(transactions_a, transactions_b)


def test_generator_creates_expected_records(portfolio):
    loans, schedule, transactions = portfolio

    assert len(loans) == 25
    assert loans["loan_id"].is_unique
    assert set(loans["status"]) == {"active"}
    assert schedule["loan_id"].isin(loans["loan_id"]).all()
    assert transactions["loan_id"].isin(loans["loan_id"]).all()


def test_loan_snapshot_has_required_metrics(portfolio):
    loans, schedule, transactions = portfolio
    snapshot = loan_snapshot(loans, schedule, transactions, "2026-11-07")

    assert len(snapshot) == 25
    assert {"dpd", "outstanding_principal_kes", "segment"}.issubset(snapshot.columns)
    assert snapshot["dpd"].ge(0).all()
    assert snapshot["outstanding_principal_kes"].ge(0).all()


def test_monthly_metrics_calculation(portfolio):
    loans, schedule, transactions = portfolio
    monthly = monthly_metrics(loans, schedule, transactions)

    assert not monthly.empty
    assert {"month", "disbursements_kes", "expected_collections_kes", "actual_collections_kes", "collection_rate"}.issubset(monthly.columns)
    assert monthly["disbursements_kes"].ge(0).all()
    assert monthly["collection_rate"].ge(0).all()
