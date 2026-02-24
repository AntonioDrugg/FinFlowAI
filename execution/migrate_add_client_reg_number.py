#!/usr/bin/env python3
"""
Migration: add client_reg_number column to the clients table.
Idempotent -- safe to run multiple times.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# Add column only if it doesn't already exist
cols = [row[1] for row in cur.execute("PRAGMA table_info(clients)").fetchall()]
if "client_reg_number" not in cols:
    cur.execute("ALTER TABLE clients ADD COLUMN client_reg_number TEXT NOT NULL DEFAULT ''")
    con.commit()
    print("Column 'client_reg_number' added to clients table.")
else:
    print("Column 'client_reg_number' already exists -- nothing to do.")

con.close()
