# Data dictionary

All money fields are denominated in Kenyan shillings (KES). Dates are calendar dates without a time zone. The generator produces synthetic records only.

## `loans.csv` / `loans`

| Field | Type | Meaning |
|---|---|---|
| `loan_id` | string | Unique synthetic loan identifier. |
| `borrower_id` | string | Synthetic borrower identifier; the generator creates one borrower per loan. |
| `segment` | string | Merchant segment: Retail, Agriculture, Food & Hospitality, Transport, or Wholesale. |
| `county` | string | Synthetic Kenyan county allocation. |
| `disbursement_date` | date | Date the loan is simulated as funded. |
| `principal_kes` | decimal | Original principal funded. |
| `annual_interest_rate` | decimal | Annualized synthetic simple-interest assumption, e.g. `0.18` means 18%. |
| `term_months` | integer | Scheduled installment count and nominal term in months. |
| `status` | string | Synthetic status field; generated loans are marked `active`. |

## `repayment_schedule.csv` / `repayment_schedule`

| Field | Type | Meaning |
|---|---|---|
| `installment_id` | string | Unique synthetic installment identifier. |
| `loan_id` | string | Loan identifier referencing `loans.loan_id`. |
| `due_date` | date | Scheduled calendar due date. |
| `installment_number` | integer | Sequence number within the loan, starting at 1. |
| `expected_amount_kes` | decimal | Total scheduled installment including the generator's synthetic interest charge. |
| `principal_due_kes` | decimal | Flat scheduled principal component used to estimate remaining principal. |

## `transactions.csv` / `transactions`

| Field | Type | Meaning |
|---|---|---|
| `transaction_id` | string | Unique simulated collection transaction identifier. |
| `loan_id` | string | Loan identifier receiving the simulated payment. |
| `transaction_date` | date | Date cash is simulated as received. |
| `amount_kes` | decimal | Cash amount received. |
| `channel` | string | Simulated collection channel: M-Pesa, USSD, or Bank. |

## Derived metric definitions

| Metric | Definition |
|---|---|
| DPD | Calendar days from the as-of date to the oldest installment due on or before that date with an unpaid balance after FIFO payment allocation. Zero if none is overdue. |
| Estimated outstanding principal | Sum of each installment's unpaid fraction multiplied by its scheduled principal component. This is a simplified portfolio estimate, not an amortized accounting balance. |
| PAR 30 / 60 / 90 | Estimated outstanding principal of loans with DPD >= 30 / 60 / 90 divided by total estimated outstanding principal on the same as-of date. |
| Expected collections | Installment amounts due in the reporting period. |
| Actual collections | Transaction amounts received in the reporting period. |
| Collection rate | Actual collections divided by expected collections for the same calendar month; late cash may therefore fall in a later month than the installment due date. |
| 90+ DPD loan rate by segment | Number of loans in the segment with DPD >= 90 divided by all loans in that segment in the as-of snapshot. |
