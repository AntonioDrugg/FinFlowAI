#!/usr/bin/env python3
"""
FinFlowAI — DB Migration: Create 'clients' table.
Safe to run multiple times (idempotent).
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id         INTEGER  PRIMARY KEY AUTOINCREMENT,
        name       TEXT     NOT NULL,
        email      TEXT     NOT NULL DEFAULT '',
        phone      TEXT     NOT NULL DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
con.commit()
con.close()
print("Migration complete: 'clients' table ready.")
