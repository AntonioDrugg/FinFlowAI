#!/usr/bin/env python3
"""
FinFlowAI — Space Settings Manager
====================================
CRUD for the space_settings table.

Each space has exactly one row.  Fields:
  tain   – Tax Advisor Identification Number
  ros_id – ROS (Revenue Online Service) Identification
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / ".tmp" / "finflowai.db"

WRITABLE_FIELDS = {"tain", "ros_id"}


def _get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Public API ─────────────────────────────────────────────────────────────────

def get_settings(space: str) -> dict:
    """
    Return the settings dict for a space.
    If no row exists yet, returns an empty-field dict (does NOT insert).
    """
    space = space.strip().lower()
    con = _get_connection()
    try:
        cur = con.cursor()
        cur.execute("SELECT * FROM space_settings WHERE space = ?", (space,))
        row = cur.fetchone()
        if row:
            return dict(row)
        # No row yet — return defaults
        return {"space": space, "tain": "", "ros_id": "", "updated_at": None}
    finally:
        con.close()


def upsert_settings(space: str, tain: str = None, ros_id: str = None) -> dict:
    """
    Create or update settings for a space.
    Pass only the fields you want to change; omit (None) to leave them unchanged.
    Returns the updated record.
    Raises ValueError if no writable field is provided.
    """
    space = space.strip().lower()
    updates = {}
    if tain   is not None: updates["tain"]   = tain.strip()
    if ros_id is not None: updates["ros_id"] = ros_id.strip()

    if not updates:
        raise ValueError("At least one of 'tain' or 'ros_id' must be provided.")

    now = _utc_now()
    con = _get_connection()
    try:
        cur = con.cursor()
        # Ensure the row exists
        cur.execute(
            "INSERT OR IGNORE INTO space_settings (space, updated_at) VALUES (?, ?)",
            (space, now),
        )
        # Apply each field individually
        for field, value in updates.items():
            cur.execute(
                f"UPDATE space_settings SET {field} = ?, updated_at = ? WHERE space = ?",
                (value, now, space),
            )
        con.commit()
        cur.execute("SELECT * FROM space_settings WHERE space = ?", (space,))
        return dict(cur.fetchone())
    finally:
        con.close()
