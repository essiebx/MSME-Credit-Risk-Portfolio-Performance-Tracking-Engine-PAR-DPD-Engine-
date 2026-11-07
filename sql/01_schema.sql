-- DuckDB-compatible logical schema for the generated CSV files.
CREATE TABLE IF NOT EXISTS loans (
    loan_id VARCHAR PRIMARY KEY,
    borrower_id VARCHAR NOT NULL,
    segment VARCHAR NOT NULL,
    county VARCHAR NOT NULL,
    disbursement_date DATE NOT NULL,
    principal_kes DOUBLE NOT NULL,
    annual_interest_rate DOUBLE NOT NULL,
    term_months INTEGER NOT NULL,
    status VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS repayment_schedule (
    installment_id VARCHAR PRIMARY KEY,
    loan_id VARCHAR NOT NULL,
    due_date DATE NOT NULL,
    installment_number INTEGER NOT NULL,
    expected_amount_kes DOUBLE NOT NULL,
    principal_due_kes DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR PRIMARY KEY,
    loan_id VARCHAR NOT NULL,
    transaction_date DATE NOT NULL,
    amount_kes DOUBLE NOT NULL,
    channel VARCHAR NOT NULL
);
