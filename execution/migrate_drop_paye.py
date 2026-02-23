#!/usr/bin/env python3
"""
FinFlowAI — DB Migration: Drop paye_agent_name and paye_tain columns.
Requires SQLite 3.35+ (shipped with Python 3.10+).
Safe to run multiple times (idempotent).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"

COLS_TO_DROP = ["paye_agent_name", "paye_tain"]

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

existing = {row[1] for row in cur.execute("PRAGMA table_info(clients)").fetchall()}
dropped = []

for col in COLS_TO_DROP:
    if col in existing:
        cur.execute(f"ALTER TABLE clients DROP COLUMN {col}")
        dropped.append(col)

con.commit()
con.close()

if dropped:
    print(f"Migration complete. Dropped columns: {', '.join(dropped)}")
else:
    print("Columns already removed — nothing to do.")
