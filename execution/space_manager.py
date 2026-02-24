#!/usr/bin/env python3
"""
FinFlowAI -- Space Manager
CRUD operations on the `spaces` table.

Each space has:
  - name  : unique identifier, lower-case kebab (e.g. "ge-souza-tax")
  - code  : exactly 2 uppercase letters, unique   (e.g. "GE")
"""
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / ".tmp" / "finflowai.db"


def get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


# ── Helpers ────────────────────────────────────────────────────────────────────

def _validate_code(code: str) -> str:
    code = code.strip().upper()
    if len(code) != 2 or not code.isalpha():
        raise ValueError("Space code must be exactly 2 letters (e.g. GE).")
    return code


def _validate_name(name: str) -> str:
    name = name.strip().lower()
    if not name:
        raise ValueError("Space name is required.")
    return name


# ── Read ───────────────────────────────────────────────────────────────────────

def space_exists(name: str) -> bool:
    """Return True if a space with the given name exists."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM spaces WHERE name = ?", (_validate_name(name),))
        return cur.fetchone() is not None
    finally:
        con.close()


def get_space(name: str) -> dict | None:
    """Return the space record for *name*, or None."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM spaces WHERE name = ?", (_validate_name(name),))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def list_spaces() -> list[dict]:
    """Return all spaces ordered by name."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM spaces ORDER BY name")
        return [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


# ── Write ──────────────────────────────────────────────────────────────────────

def create_space(name: str, code: str) -> dict:
    """
    Create a new space.  Raises ValueError on:
      - invalid name or code
      - duplicate name
      - duplicate code
    """
    name = _validate_name(name)
    code = _validate_code(code)

    con = get_connection()
    try:
        cur = con.cursor()
        # duplicate name check
        cur.execute("SELECT id FROM spaces WHERE name = ?", (name,))
        if cur.fetchone():
            raise ValueError(f"Space '{name}' already exists.")
        # duplicate code check
        cur.execute("SELECT id, name FROM spaces WHERE code = ?", (code,))
        row = cur.fetchone()
        if row:
            raise ValueError(f"Code '{code}' is already used by space '{row['name']}'.")

        cur.execute(
            "INSERT INTO spaces (name, code) VALUES (?, ?)",
            (name, code),
        )
        con.commit()
        cur.execute("SELECT * FROM spaces WHERE id = ?", (cur.lastrowid,))
        return dict(cur.fetchone())
    finally:
        con.close()


def delete_space(name: str) -> bool:
    """Delete a space by name. Returns True if deleted."""
    name = _validate_name(name)
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM spaces WHERE name = ?", (name,))
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()
