# Directive: Ingest Financial Transactions

## Goal
Import transaction data from a source (CSV file, manual entry, or bank API) and store it in a standardised format for analysis.

## Inputs
- A CSV file at `.tmp/transactions_raw.csv`, **or**
- Manual entry via the web UI

## Expected CSV Format
```
date,description,amount,category
2026-01-15,Tesco,-42.30,Groceries
2026-01-16,Salary,3200.00,Income
2026-01-17,Netflix,-15.99,Subscriptions
```

## Script to Use
`execution/ingest_transactions.py`

## Steps
1. Validate the input CSV has the required columns: `date`, `description`, `amount`, `category`
2. Parse dates to ISO 8601 format
3. Classify positive amounts as income, negative as expenses
4. Write cleaned data to `.tmp/transactions_clean.json`
5. Print a summary: total income, total expenses, net cash flow

## Outputs
- `.tmp/transactions_clean.json` — cleaned, normalised transaction list
- Console summary printed to stdout

## Edge Cases & Notes
- If `category` column is missing, default to "Uncategorised"
- Ignore rows where `amount` is 0
- If a date cannot be parsed, skip the row and log a warning
- Handle both comma and semicolon delimiters

## Update Log
- 2026-02-21: Directive created
