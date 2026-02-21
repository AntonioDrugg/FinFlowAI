#!/usr/bin/env python3
"""
FinFlowAI — Transaction Ingestion Script
Reads a raw CSV of financial transactions, validates and cleans the data,
then writes a normalised JSON file to .tmp/.

Usage:
    python execution/ingest_transactions.py [path/to/transactions.csv]

If no path is provided, defaults to .tmp/transactions_raw.csv
"""

import sys
import os
import json
import csv
import logging
from datetime import datetime
from pathlib import Path

# ── Setup ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / ".tmp"
TMP_DIR.mkdir(exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"date", "description", "amount"}

# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_date(raw: str) -> str | None:
    """Try common date formats and return ISO 8601, or None on failure."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def detect_delimiter(filepath: Path) -> str:
    """Sniff CSV delimiter (comma or semicolon)."""
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        sample = f.read(2048)
    return ";" if sample.count(";") > sample.count(",") else ","


def ingest(filepath: Path) -> list[dict]:
    delimiter = detect_delimiter(filepath)
    transactions = []
    skipped = 0

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = {h.strip().lower() for h in (reader.fieldnames or [])}

        missing = REQUIRED_COLUMNS - headers
        if missing:
            log.error(f"CSV is missing required columns: {missing}")
            sys.exit(1)

        for i, row in enumerate(reader, start=2):  # row 1 = header
            row = {k.strip().lower(): v.strip() for k, v in row.items()}

            # Parse date
            date = parse_date(row.get("date", ""))
            if not date:
                log.warning(f"Row {i}: could not parse date '{row.get('date')}' — skipping")
                skipped += 1
                continue

            # Parse amount
            try:
                amount = float(row["amount"].replace(",", ""))
            except ValueError:
                log.warning(f"Row {i}: invalid amount '{row['amount']}' — skipping")
                skipped += 1
                continue

            if amount == 0:
                skipped += 1
                continue

            transactions.append({
                "date": date,
                "description": row.get("description", ""),
                "amount": amount,
                "category": row.get("category", "Uncategorised"),
                "type": "income" if amount > 0 else "expense",
            })

    log.info(f"Processed {len(transactions)} transactions, skipped {skipped} rows.")
    return transactions


def summarise(transactions: list[dict]) -> None:
    income = sum(t["amount"] for t in transactions if t["type"] == "income")
    expenses = sum(abs(t["amount"]) for t in transactions if t["type"] == "expense")
    net = income - expenses
    print("\n──────────────────────────────")
    print(f"  💰  Total Income:   £{income:,.2f}")
    print(f"  💸  Total Expenses: £{expenses:,.2f}")
    print(f"  📊  Net Cash Flow:  £{net:,.2f}")
    print("──────────────────────────────\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else TMP_DIR / "transactions_raw.csv"

    if not input_path.exists():
        log.error(f"Input file not found: {input_path}")
        sys.exit(1)

    log.info(f"Ingesting transactions from: {input_path}")
    transactions = ingest(input_path)

    output_path = TMP_DIR / "transactions_clean.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transactions, f, indent=2)

    log.info(f"Cleaned data saved to: {output_path}")
    summarise(transactions)


if __name__ == "__main__":
    main()
