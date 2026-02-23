#!/usr/bin/env python3
"""
FinFlowAI — Client Manager
CRUD operations for the full client profile.

FinFlow Number is derived from the record id: FF-{id:04d}
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / ".tmp" / "finflowai.db"

# All writable fields (order matches the form sections)
CLIENT_FIELDS = [
    "name",
    "civil_status",
    "pps_number",
    "date_of_birth",
    "revenue_password",
    "email",
    "mobile",
    "other_phone",
    "address_line1",
    "address_line2",
    "address_line3",
    "city_county",
    "eir_code",
    "bank_holder_name",
    "bank_iban",
    "bank_bic",
    "paye_agent_name",
    "paye_tain",
]


def get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _finflow_number(record_id: int) -> str:
    return f"FF-{record_id:04d}"


def _enrich(record: dict) -> dict:
    """Add the computed finflow_number field."""
    record["finflow_number"] = _finflow_number(record["id"])
    return record


def add_client(data: dict) -> dict:
    """
    Add a new client. `data` is a dict with any subset of CLIENT_FIELDS.
    `name` is required. Returns the created record (with finflow_number).
    """
    name = data.get("name", "").strip()
    if not name:
        raise ValueError("Client name is required.")

    cols   = []
    values = []
    for field in CLIENT_FIELDS:
        cols.append(field)
        values.append(data.get(field, "").strip() if isinstance(data.get(field, ""), str) else "")

    con = get_connection()
    try:
        cur = con.cursor()
        placeholders = ", ".join("?" * len(cols))
        col_str = ", ".join(cols)
        cur.execute(
            f"INSERT INTO clients ({col_str}) VALUES ({placeholders})",
            values,
        )
        con.commit()
        cur.execute("SELECT * FROM clients WHERE id = ?", (cur.lastrowid,))
        return _enrich(dict(cur.fetchone()))
    finally:
        con.close()


def list_clients() -> list[dict]:
    """Return all clients, most recent first, with finflow_number."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM clients ORDER BY id DESC")
        return [_enrich(dict(r)) for r in cur.fetchall()]
    finally:
        con.close()


def get_client(client_id: int) -> dict | None:
    """Return a single client by id, or None."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        row = cur.fetchone()
        return _enrich(dict(row)) if row else None
    finally:
        con.close()


def update_client(client_id: int, data: dict) -> dict | None:
    """Update an existing client. Returns updated record or None if not found."""
    con = get_connection()
    try:
        cur = con.cursor()
        sets   = []
        values = []
        for field in CLIENT_FIELDS:
            if field in data:
                sets.append(f"{field} = ?")
                values.append(data[field].strip() if isinstance(data[field], str) else "")
        if not sets:
            return get_client(client_id)
        values.append(client_id)
        cur.execute(
            f"UPDATE clients SET {', '.join(sets)} WHERE id = ?",
            values,
        )
        con.commit()
        if cur.rowcount == 0:
            return None
        cur.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        return _enrich(dict(cur.fetchone()))
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
