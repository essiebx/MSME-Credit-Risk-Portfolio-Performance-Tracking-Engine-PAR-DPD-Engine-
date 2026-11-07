-- Loan-level DPD and estimated principal balance at a selected snapshot date.
-- Change the DATE literal below, or substitute it from your application.
WITH params AS (
    SELECT DATE '2026-11-07' AS as_of_date
), eligible_loans AS (
    SELECT l.*
    FROM loans l CROSS JOIN params p
    WHERE l.disbursement_date <= p.as_of_date
), paid AS (
    SELECT t.loan_id, SUM(t.amount_kes) AS total_paid_kes
    FROM transactions t CROSS JOIN params p
    WHERE t.transaction_date <= p.as_of_date
    GROUP BY t.loan_id
), running_schedule AS (
    SELECT s.*,
           SUM(s.expected_amount_kes) OVER (
               PARTITION BY s.loan_id ORDER BY s.due_date, s.installment_number
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
           ) AS cumulative_expected_kes
    FROM repayment_schedule s
), allocated AS (
    SELECT r.*,
           COALESCE(p.total_paid_kes, 0) AS total_paid_kes,
           GREATEST(0, r.cumulative_expected_kes - COALESCE(p.total_paid_kes, 0)) AS remaining_after_kes,
           GREATEST(0, r.cumulative_expected_kes - r.expected_amount_kes - COALESCE(p.total_paid_kes, 0)) AS remaining_before_kes
    FROM running_schedule r
    LEFT JOIN paid p USING (loan_id)
), installment_balance AS (
    SELECT *, GREATEST(0, remaining_after_kes - remaining_before_kes) AS unpaid_installment_kes
    FROM allocated
), loan_status AS (
    SELECT e.loan_id, e.borrower_id, e.segment, e.county, e.disbursement_date,
           e.principal_kes,
           COALESCE(MAX(CASE WHEN i.due_date <= p.as_of_date AND i.unpaid_installment_kes > 0.01
                             THEN DATE_DIFF('day', i.due_date, p.as_of_date) ELSE 0 END), 0) AS dpd,
           COALESCE(SUM(i.unpaid_installment_kes / NULLIF(i.expected_amount_kes, 0)
                        * i.principal_due_kes), 0) AS outstanding_principal_kes
    FROM eligible_loans e
    CROSS JOIN params p
    LEFT JOIN installment_balance i USING (loan_id)
    GROUP BY e.loan_id, e.borrower_id, e.segment, e.county, e.disbursement_date, e.principal_kes
)
SELECT *,
       CASE WHEN dpd >= 90 THEN '90+'
            WHEN dpd >= 60 THEN '60-89'
            WHEN dpd >= 30 THEN '30-59'
            WHEN dpd > 0 THEN '1-29'
            ELSE 'Current' END AS dpd_bucket
FROM loan_status
ORDER BY dpd DESC, loan_id;
