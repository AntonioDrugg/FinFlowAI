#!/usr/bin/env python3
"""
FinFlowAI — DB Migration: Add 'name' column to users table.
Safe to run multiple times (idempotent).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cols = [row[1] for row in cur.execute("PRAGMA table_info(users)").fetchall()]
print("Current columns:", cols)

if "name" not in cols:
    cur.execute('ALTER TABLE users ADD COLUMN name TEXT NOT NULL DEFAULT ""')
    con.commit()
    print("Migration complete: column 'name' added.")
else:
    print("Column 'name' already exists — nothing to do.")

con.close()
