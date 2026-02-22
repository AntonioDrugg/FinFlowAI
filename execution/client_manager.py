#!/usr/bin/env python3
"""
FinFlowAI — Client Manager
CRUD operations for the clients table.
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / ".tmp" / "finflowai.db"


def get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def add_client(name: str, email: str = "", phone: str = "") -> dict:
    """Add a new client. Returns the created record."""
    name  = name.strip()
    email = email.strip()
    phone = phone.strip()
    if not name:
        raise ValueError("Client name is required.")

    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO clients (name, email, phone) VALUES (?, ?, ?)",
            (name, email, phone),
        )
        con.commit()
        cur.execute("SELECT * FROM clients WHERE id = ?", (cur.lastrowid,))
        return dict(cur.fetchone())
    finally:
        con.close()


def list_clients() -> list[dict]:
    """Return all clients ordered by most recently added."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM clients ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


def delete_client(client_id: int) -> bool:
    """Delete a client by ID. Returns True if deleted."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()
