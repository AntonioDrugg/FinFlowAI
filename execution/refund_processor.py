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

def check_single_client_api(client_id: int, space: str, cert_bytes: bytes, cert_password: str) -> dict:
    ran_at = _utc_now()
    client = _fetch_client(client_id, space)
    
    if client is None:
        return {
            "client_id":      client_id,
            "finflow_number": "—",
            "name":           f"(ID {client_id})",
            "pps_number":     "—",
            "status":         "error",
            "message":        f"Client ID {client_id} not found in space '{space}'.",
            "detail":         {},
            "ran_at":         ran_at,
        }

    # Fetch Space TAIN
    import space_settings_manager as ssm
    space_settings = ssm.get_settings(space)
    tain = space_settings.get("tain")
    
    if not tain:
        return {
            "client_id":      client["id"],
            "finflow_number": client.get("finflow_number", "—"),
            "name":           client.get("name", "—"),
            "pps_number":     client.get("pps_number", "—"),
            "status":         "error",
            "message":        f"No TAIN configured for space '{space}'. Please update Space Setup.",
            "detail":         {},
            "ran_at":         ran_at,
        }

    pps_number = client.get("pps_number", "")
    if not pps_number:
        return {
            "client_id":      client["id"],
            "finflow_number": client.get("finflow_number", "—"),
            "name":           client.get("name", "—"),
            "pps_number":     "—",
            "status":         "error",
            "message":        "Client has no PPS number.",
            "detail":         {},
            "ran_at":         ran_at,
        }

    # API Payload structure (mocked)
    payload = {
        "clientPPS": pps_number.strip(),
        "taxType": "PAYE",
        "taxYear": datetime.now(timezone.utc).year,
        "clientRegistrationRef": pps_number.strip(),
        "agentTAIN": tain
    }

    # ------------------------------------------------------------------ MOCK API CALL --
    # Here is where the code would authenticate using cert_bytes and cert_password
    # and send the payload to the Irish Revenue API.
    
    outcome = {
        "status":  "success",
        "message": "Mocked successful refund check from Irish Revenue.",
        "detail":  {
            "payload_sent": payload,
            "refund_amount": "€0.00",
            "tax_year": payload["taxYear"]
        }
    }
    # ------------------------------------------------------------------ /MOCK API CALL -

    return {
        "client_id":      client["id"],
        "finflow_number": client.get("finflow_number", "—"),
        "name":           client.get("name", "—"),
        "pps_number":     pps_number.strip(),
        "status":         outcome["status"],
        "message":        outcome["message"],
        "detail":         outcome.get("detail", {}),
        "ran_at":         ran_at,
    }
