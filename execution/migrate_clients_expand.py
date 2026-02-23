#!/usr/bin/env python3
"""
FinFlowAI — DB Migration: Expand clients table with full client profile fields.
Safe to run multiple times (idempotent).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"

NEW_COLUMNS = [
    ("civil_status",     "TEXT NOT NULL DEFAULT ''"),
    ("pps_number",       "TEXT NOT NULL DEFAULT ''"),
    ("date_of_birth",    "TEXT NOT NULL DEFAULT ''"),
    ("revenue_password", "TEXT NOT NULL DEFAULT ''"),
    ("address_line1",    "TEXT NOT NULL DEFAULT ''"),
    ("address_line2",    "TEXT NOT NULL DEFAULT ''"),
    ("address_line3",    "TEXT NOT NULL DEFAULT ''"),
    ("city_county",      "TEXT NOT NULL DEFAULT ''"),
    ("eir_code",         "TEXT NOT NULL DEFAULT ''"),
    # email already exists — skip
    ("mobile",           "TEXT NOT NULL DEFAULT ''"),
    ("other_phone",      "TEXT NOT NULL DEFAULT ''"),
    ("bank_holder_name", "TEXT NOT NULL DEFAULT ''"),
    ("bank_iban",        "TEXT NOT NULL DEFAULT ''"),
    ("bank_bic",         "TEXT NOT NULL DEFAULT ''"),
    ("paye_agent_name",  "TEXT NOT NULL DEFAULT ''"),
    ("paye_tain",        "TEXT NOT NULL DEFAULT ''"),
]

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

existing = {row[1] for row in cur.execute("PRAGMA table_info(clients)").fetchall()}
added = []

for col_name, col_def in NEW_COLUMNS:
    if col_name not in existing:
        cur.execute(f"ALTER TABLE clients ADD COLUMN {col_name} {col_def}")
        added.append(col_name)

con.commit()
con.close()

if added:
    print(f"Migration complete. Added columns: {', '.join(added)}")
else:
    print("All columns already present — nothing to do.")
