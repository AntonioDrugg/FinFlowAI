#!/usr/bin/env python3
"""
FinFlowAI — Database Setup
Creates the SQLite database and users table (idempotent — safe to run multiple times).

Usage:
    python execution/setup_db.py
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR  = BASE_DIR / ".tmp"
DB_PATH  = TMP_DIR / "finflowai.db"


def setup():
    TMP_DIR.mkdir(exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            space         TEXT    NOT NULL,
            login         TEXT    NOT NULL,
            password_hash TEXT    NOT NULL,
            name          TEXT    NOT NULL DEFAULT "",
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(space, login, password_hash)
        );
    """)

    con.commit()
    con.close()
    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    setup()
