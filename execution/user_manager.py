#!/usr/bin/env python3
"""
FinFlowAI — User / Credential Manager
Handles all CRUD operations on the users table.

Passwords are stored as SHA-256(password + APP_SECRET) — deterministic,
so uniqueness can be enforced at the database level on the triple
(space, login, password_hash).

CLI Usage:
    python execution/user_manager.py add    --space acme --login alice --password secret --name Alice
    python execution/user_manager.py verify --space acme --login alice --password secret
    python execution/user_manager.py list   [--space acme]
    python execution/user_manager.py delete --id 3
"""

import argparse
import hashlib
import os
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / ".tmp" / "finflowai.db"

# ── Secret salt (override via APP_SECRET env var) ─────────────────────────────
APP_SECRET = os.getenv("APP_SECRET", "finflowai-default-secret-change-in-production")


# ── Helpers ────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Deterministic SHA-256 hash of password + app secret."""
    raw = f"{password}{APP_SECRET}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        print("ERROR: Database not found. Run `python execution/setup_db.py` first.")
        sys.exit(1)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def normalise(value: str) -> str:
    """Strip and lowercase for consistent comparison."""
    return value.strip().lower()


# ── CRUD ───────────────────────────────────────────────────────────────────────

def add_user(space: str, login: str, password: str, name: str = "") -> dict:
    """
    Add a new credential triple. Returns the new record on success.
    Raises ValueError if the exact triple already exists.
    """
    space = normalise(space)
    login = normalise(login)
    name  = name.strip()
    password_hash = hash_password(password)

    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users (space, login, password_hash, name) VALUES (?, ?, ?, ?)",
            (space, login, password_hash, name),
        )
        con.commit()
        row_id = cur.lastrowid
        cur.execute("SELECT * FROM users WHERE id = ?", (row_id,))
        record = dict(cur.fetchone())
        return record
    except sqlite3.IntegrityError:
        raise ValueError(
            f"A record with space='{space}', login='{login}', and that password already exists."
        )
    finally:
        con.close()


def verify_user(space: str, login: str, password: str) -> bool:
    """Return True if the exact (space, login, password) triple exists."""
    space = normalise(space)
    login = normalise(login)
    password_hash = hash_password(password)

    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT id FROM users WHERE space = ? AND login = ? AND password_hash = ?",
            (space, login, password_hash),
        )
        return cur.fetchone() is not None
    finally:
        con.close()


def get_user(space: str, login: str, password: str) -> dict | None:
    """
    Return the full user record if the exact (space, login, password) triple
    exists, or None if no match is found.
    The password_hash is excluded from the returned dict.
    """
    space = normalise(space)
    login = normalise(login)
    password_hash = hash_password(password)

    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            """SELECT id, space, login, name, created_at
               FROM users
               WHERE space = ? AND login = ? AND password_hash = ?""",
            (space, login, password_hash),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        con.close()


def list_users(space: str | None = None) -> list[dict]:
    """Return all credential records, optionally filtered by space."""
    con = get_connection()
    try:
        cur = con.cursor()
        if space:
            cur.execute(
                "SELECT id, space, login, name, created_at FROM users WHERE space = ? ORDER BY space, login",
                (normalise(space),),
            )
        else:
            cur.execute(
                "SELECT id, space, login, name, created_at FROM users ORDER BY space, login"
            )
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()


def delete_user(record_id: int) -> bool:
    """Delete a record by ID. Returns True if a row was deleted."""
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("DELETE FROM users WHERE id = ?", (record_id,))
        con.commit()
        return cur.rowcount > 0
    finally:
        con.close()


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FinFlowAI User Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Add a credential record")
    p_add.add_argument("--space",    required=True)
    p_add.add_argument("--login",    required=True)
    p_add.add_argument("--password", required=True)
    p_add.add_argument("--name",     default="", help="Display name for the user")

    # verify
    p_ver = sub.add_parser("verify", help="Check if a credential triple exists")
    p_ver.add_argument("--space",    required=True)
    p_ver.add_argument("--login",    required=True)
    p_ver.add_argument("--password", required=True)

    # list
    p_lst = sub.add_parser("list", help="List all records")
    p_lst.add_argument("--space", default=None, help="Filter by space")

    # delete
    p_del = sub.add_parser("delete", help="Delete a record by ID")
    p_del.add_argument("--id", type=int, required=True)

    args = parser.parse_args()

    if args.command == "add":
        try:
            record = add_user(args.space, args.login, args.password, args.name)
            print(f"Added: id={record['id']}  space={record['space']}  login={record['login']}  name={record['name']}")
        except ValueError as e:
            print(f"DUPLICATE: {e}")
            sys.exit(1)

    elif args.command == "verify":
        ok = verify_user(args.space, args.login, args.password)
        print("VALID" if ok else "INVALID")
        sys.exit(0 if ok else 1)

    elif args.command == "list":
        rows = list_users(args.space)
        if not rows:
            print("No records found.")
        else:
            print(f"{'ID':<5} {'SPACE':<20} {'LOGIN':<30} {'NAME':<20} {'CREATED'}")
            print("-" * 85)
            for r in rows:
                print(f"{r['id']:<5} {r['space']:<20} {r['login']:<30} {r['name']:<20} {r['created_at']}")

    elif args.command == "delete":
        deleted = delete_user(args.id)
        print(f"Deleted record {args.id}." if deleted else f"No record with id={args.id}.")


if __name__ == "__main__":
    main()
