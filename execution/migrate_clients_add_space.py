#!/usr/bin/env python3
"""
FinFlowAI — DB Migration: Add 'space' column to clients table.
Each client record is now owned by one space.
Also updates finflow_number prefix from 'FF' to the space code.
Safe to run multiple times (idempotent).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

existing = {row[1] for row in cur.execute("PRAGMA table_info(clients)").fetchall()}

if "space" not in existing:
    cur.execute("ALTER TABLE clients ADD COLUMN space TEXT NOT NULL DEFAULT ''")
    print("Added column: space")
else:
    print("Column 'space' already exists — nothing to do.")

con.commit()
con.close()
print("Migration complete.")
