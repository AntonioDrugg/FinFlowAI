#!/usr/bin/env python3
"""
FinFlowAI — Refund Processor
=============================
Standalone module for the Refunds Check process.

Architecture:
  - run_refunds(client_ids, space) → generator that yields one result dict per client
  - Each result has a fixed schema so the API and UI can depend on it
  - The actual refund-check logic lives in _check_single_client() — to be implemented
    in the next phase. Right now it returns a 'pending' status as a placeholder.

Return schema per client:
  {
    "client_id":      int,
    "finflow_number": str,
    "name":           str,
    "pps_number":     str,
    "status":         "success" | "error" | "pending" | "no_data",
    "message":        str,   # human-readable result summary
    "detail":         dict,  # process-specific payload (empty until logic is wired up)
    "ran_at":         str,   # ISO-8601 UTC timestamp
  }
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / ".tmp" / "finflowai.db"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_connection() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fetch_client(client_id: int, space: str) -> dict | None:
    """Return a client dict or None if not found in the space."""
    con = _get_connection()
    try:
        cur = con.cursor()
        cur.execute(
            "SELECT * FROM clients WHERE id = ? AND space = ?",
            (client_id, space.strip().lower()),
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        con.close()


# ── Core refund logic (STUB — to be implemented) ───────────────────────────────

def _check_single_client(client: dict) -> dict:
    """
    Perform the refund check for one client.

    THIS IS A STUB. Implementation will be added in the next phase.
    When implemented, this function should:
      - Log into Revenue Online (or query the appropriate API/source)
      - Check refund status for the client's PPS number
      - Return the structured result below

    Args:
        client: Full client record dict from the database.

    Returns:
        {
            "status":  "success" | "error" | "pending" | "no_data",
            "message": str,
            "detail":  dict,   # e.g. {"refund_amount": "€1,234.00", "tax_year": 2023}
        }
    """
    # ------------------------------------------------------------------ STUB --
    return {
        "status":  "pending",
        "message": "Refund check not yet implemented. Logic will be wired up in the next phase.",
        "detail":  {},
    }
    # ------------------------------------------------------------------ /STUB -


# ── Public API ─────────────────────────────────────────────────────────────────

def run_refunds(client_ids: list[int], space: str) -> list[dict]:
    """
    Run the refund check for a list of client IDs, sequentially one by one.

    Args:
        client_ids:  Ordered list of client IDs to process.
        space:       Space name (e.g. 'ge-souza-tax').

    Returns:
        List of result dicts, one per client ID, in the same order as client_ids.
        Clients not found in the space are recorded with status='error'.
    """
    results = []

    for cid in client_ids:
        ran_at = _utc_now()
        client = _fetch_client(cid, space)

        if client is None:
            results.append({
                "client_id":      cid,
                "finflow_number": "—",
                "name":           f"(ID {cid})",
                "pps_number":     "—",
                "status":         "error",
                "message":        f"Client ID {cid} not found in space '{space}'.",
                "detail":         {},
                "ran_at":         ran_at,
            })
            continue

        try:
            outcome = _check_single_client(client)
            results.append({
                "client_id":      client["id"],
                "finflow_number": client.get("finflow_number", "—"),
                "name":           client.get("name", "—"),
                "pps_number":     client.get("pps_number", "—"),
                "status":         outcome["status"],
                "message":        outcome["message"],
                "detail":         outcome.get("detail", {}),
                "ran_at":         ran_at,
            })
        except Exception as exc:
            results.append({
                "client_id":      client["id"],
                "finflow_number": client.get("finflow_number", "—"),
                "name":           client.get("name", "—"),
                "pps_number":     client.get("pps_number", "—"),
                "status":         "error",
                "message":        f"Unexpected error: {exc}",
                "detail":         {},
                "ran_at":         ran_at,
            })

    return results
