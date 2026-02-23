#!/usr/bin/env python3
"""
FinFlowAI — DB Migration: Rename legacy 'phone' column to 'legacy_phone'.
SQLite 3.25+ supports ALTER TABLE RENAME COLUMN.
Safe to run multiple times (idempotent).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cols = {row[1] for row in cur.execute("PRAGMA table_info(clients)").fetchall()}

if "phone" in cols and "legacy_phone" not in cols:
    cur.execute("ALTER TABLE clients RENAME COLUMN phone TO legacy_phone")
    con.commit()
    print("Migration complete: 'phone' renamed to 'legacy_phone'.")
elif "legacy_phone" in cols:
    print("Column already renamed — nothing to do.")
else:
    print("Column 'phone' not found — nothing to do.")

con.close()
