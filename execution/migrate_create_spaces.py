#!/usr/bin/env python3
"""
FinFlowAI -- Migration: create `spaces` table and seed ge-souza-tax / GE.
Idempotent -- safe to run multiple times.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS spaces (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL UNIQUE,
        code       TEXT NOT NULL UNIQUE,
        created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    )
""")

# Seed the first real space so existing data stays consistent
cur.execute(
    "INSERT OR IGNORE INTO spaces (name, code) VALUES (?, ?)",
    ("ge-souza-tax", "GE"),
)

con.commit()
con.close()
print("spaces table ready.  ge-souza-tax / GE seeded (ignored if already exists).")
