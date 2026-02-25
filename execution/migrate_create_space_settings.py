#!/usr/bin/env python3
"""
Migration: create the space_settings table.
Idempotent — safe to run multiple times.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / ".tmp" / "finflowai.db"
con = sqlite3.connect(DB_PATH)
cur = con.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS space_settings (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        space      TEXT    NOT NULL UNIQUE,
        tain       TEXT    NOT NULL DEFAULT '',
        ros_id     TEXT    NOT NULL DEFAULT '',
        updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
    )
""")

# Seed the existing space with empty settings if not already present
cur.execute("""
    INSERT OR IGNORE INTO space_settings (space) VALUES ('ge-souza-tax')
""")

con.commit()
con.close()
print("space_settings table ready.")
