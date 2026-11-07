-- Monthly cash-flow trends. Expected collections are grouped by due month;
-- receipts are grouped by transaction month; disbursements by funding month.
WITH monthly_events AS (
    SELECT DATE_TRUNC('month', disbursement_date)::DATE AS month,
           SUM(principal_kes) AS disbursements_kes,
           0.0 AS expected_collections_kes,
           0.0 AS actual_collections_kes
    FROM loans GROUP BY 1
    UNION ALL
    SELECT DATE_TRUNC('month', due_date)::DATE AS month,
           0.0, SUM(expected_amount_kes), 0.0
    FROM repayment_schedule GROUP BY 1
    UNION ALL
    SELECT DATE_TRUNC('month', transaction_date)::DATE AS month,
           0.0, 0.0, SUM(amount_kes)
    FROM transactions GROUP BY 1
), monthly AS (
    SELECT month, SUM(disbursements_kes) AS disbursements_kes,
           SUM(expected_collections_kes) AS expected_collections_kes,
           SUM(actual_collections_kes) AS actual_collections_kes
    FROM monthly_events GROUP BY month
)
SELECT month, disbursements_kes, expected_collections_kes, actual_collections_kes,
       actual_collections_kes / NULLIF(expected_collections_kes, 0) AS collection_rate
FROM monthly
ORDER BY month;
