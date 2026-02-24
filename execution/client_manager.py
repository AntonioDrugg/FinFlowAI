#!/usr/bin/env python3
"""
FinFlowAI — Client Manager
CRUD operations for the full client profile.

Every client belongs to a space. The FinFlow Number prefix is derived from
the space name: first two letters uppercased.
  e.g.  "ge-souza-tax"  →  "GE"  →  "GE-0001"
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / ".tmp" / "finflowai.db"

# All writable data fields (order matches the form sections)
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
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def space_code(space: str) -> str:
    """Derive the 2-letter uppercase prefix from a space name.
    'ge-souza-tax' → 'GE'   |   'abc-firm' → 'AB'   |   '' → 'FF'
    """
    s = (space or "").strip()
    return s[:2].upper() if len(s) >= 2 else (s.upper() if s else "FF")


def _finflow_number(record_id: int, space: str) -> str:
    return f"{space_code(space)}-{record_id:04d}"


def _enrich(record: dict) -> dict:
    """Add the computed finflow_number field to a record dict."""
    record["finflow_number"] = _finflow_number(record["id"], record.get("space", ""))
    return record


# ── Write operations ───────────────────────────────────────────────────────────

def add_client(data: dict, space: str) -> dict:
    """
    Add a new client for *space*.
    `data` is a dict with any subset of CLIENT_FIELDS.
    `name` is required. Returns the created record (with finflow_number).
    """
    name = data.get("name", "").strip()
    if not name:
        raise ValueError("Client name is required.")

    cols   = ["space"]
    values = [space]
    for field in CLIENT_FIELDS:
        cols.append(field)
        val = data.get(field, "")
        values.append(val.strip() if isinstance(val, str) else "")

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


def update_client(client_id: int, data: dict, space: str) -> dict | None:
    """Update an existing client (must belong to *space*). Returns updated record or None."""
    con = get_connection()
    try:
        cur = con.cursor()
        sets   = []
        values = []
        for field in CLIENT_FIELDS:
            if field in data:
                sets.append(f"{field} = ?")
                val = data[field]
                values.append(val.strip() if isinstance(val, str) else "")
        if not sets:
            return get_client(client_id, space)
        values.extend([client_id, space])
        cur.execute(
            f"UPDATE clients SET {', '.join(sets)} WHERE id = ? AND space = ?",
            values,
        )
        con.commit()
        if cur.rowcount == 0:
            return None
        cur.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        return _enrich(dict(cur.fetchone()))
    finally:
        con.close()


def delete_client(client_id: int, space: str) -> bool:
    """Delete a client by ID within *space*. Returns True if deleted."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM clients WHERE id = ? AND space = ?", (client_id, space))
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()


# ── Read operations ────────────────────────────────────────────────────────────

def list_clients(space: str) -> list[dict]:
    """Return all clients for *space*, most recent first, with finflow_number."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM clients WHERE space = ? ORDER BY id ASC", (space,))
        return [_enrich(dict(r)) for r in cur.fetchall()]
    finally:
        con.close()


def get_client(client_id: int, space: str) -> dict | None:
    """Return a single client by id within *space*, or None."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM clients WHERE id = ? AND space = ?", (client_id, space))
        row = cur.fetchone()
        return _enrich(dict(row)) if row else None
    finally:
        con.close()
