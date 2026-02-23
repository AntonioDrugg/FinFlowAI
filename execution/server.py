#!/usr/bin/env python3
"""
FinFlowAI — Flask Web Server
Serves the web UI and provides the REST API for authentication and user management.

Usage:
    python execution/server.py
    # -> http://localhost:5000
"""

import os
import sys
from pathlib import Path

# Make sure sibling scripts are importable
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "execution"))

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from dotenv import load_dotenv
import csv, io

import user_manager as um
import client_manager as cm

# ── Config ─────────────────────────────────────────────────────────────────────
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, static_folder=str(BASE_DIR / "web"))
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

WEB_DIR = BASE_DIR / "web"

# ── Static / UI ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/home.html")
def home():
    return send_from_directory(WEB_DIR, "home.html")


@app.route("/clients.html")
def clients_page():
    return send_from_directory(WEB_DIR, "clients.html")


@app.route("/processes.html")
def processes_page():
    return send_from_directory(WEB_DIR, "processes.html")


@app.route("/space-setup.html")
def space_setup_page():
    return send_from_directory(WEB_DIR, "space-setup.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(WEB_DIR, filename)


# ── API: Login ─────────────────────────────────────────────────────────────────

@app.post("/api/login")
def api_login():
    """
    POST /api/login
    Body: { "space": "...", "login": "...", "password": "..." }

    Validation rules:
      - All three fields must be present and non-empty → 400
      - The exact combination (space, login, password) must exist in the
        users table → 401 if not found, 200 if found.
      - Matching is case-insensitive (space and login are lowercased before lookup).
      - The password is SHA-256 hashed before comparison — plain text is never stored.
    """
    data = request.get_json(silent=True) or {}
    space    = data.get("space", "").strip()
    login    = data.get("login", "").strip()
    password = data.get("password", "").strip()

    # ── Field presence check ───────────────────────────────────────────────────
    missing = [f for f, v in [("space", space), ("login", login), ("password", password)] if not v]
    if missing:
        return jsonify({
            "error": f"Missing required field(s): {', '.join(missing)}."
        }), 400

    # ── Credential lookup — all three fields must match ────────────────────────
    user = um.get_user(space, login, password)
    if user is None:
        # Deliberately vague — do not reveal which field was wrong
        return jsonify({
            "error": "Invalid credentials. Please check your Space, Login, and Password."
        }), 401

    # ── Success ────────────────────────────────────────────────────────────────
    display_name = user.get("name") or user["login"]
    return jsonify({
        "success": True,
        "message": f"Welcome, {display_name}!",
        "user": {
            "id":    user["id"],
            "space": user["space"],
            "login": user["login"],
            "name":  user.get("name", ""),
        }
    }), 200


# ── API: Users ─────────────────────────────────────────────────────────────────

@app.get("/api/users")
def api_list_users():
    """
    GET /api/users?space=<optional>
    Returns all credential records (without password hashes).
    """
    space = request.args.get("space", None)
    rows = um.list_users(space)
    return jsonify(rows), 200


@app.post("/api/users")
def api_add_user():
    """
    POST /api/users
    Body: { "space": "...", "login": "...", "password": "..." }
    Returns 201 on success, 409 on duplicate, 400 on missing fields.
    """
    data = request.get_json(silent=True) or {}
    space    = data.get("space", "").strip()
    login    = data.get("login", "").strip()
    password = data.get("password", "").strip()
    name     = data.get("name", "").strip()

    if not all([space, login, password]):
        return jsonify({"error": "All fields (space, login, password) are required."}), 400

    try:
        record = um.add_user(space, login, password, name)
        # Don't return the hash
        record.pop("password_hash", None)
        return jsonify(record), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@app.delete("/api/users/<int:record_id>")
def api_delete_user(record_id: int):
    """
    DELETE /api/users/<id>
    Returns 200 if deleted, 404 if not found.
    """
    deleted = um.delete_user(record_id)
    if deleted:
        return jsonify({"message": f"Record {record_id} deleted."}), 200
    else:
        return jsonify({"error": f"No record with id={record_id}."}), 404


# ── API: Clients ───────────────────────────────────────────────────────────────

@app.get("/api/clients")
def api_list_clients():
    """GET /api/clients — return all clients."""
    return jsonify(cm.list_clients()), 200


@app.get("/api/clients/<int:client_id>")
def api_get_client(client_id: int):
    """GET /api/clients/<id> — return a single client."""
    record = cm.get_client(client_id)
    if record:
        return jsonify(record), 200
    return jsonify({"error": f"No client with id={client_id}."}), 404


@app.post("/api/clients")
def api_add_client():
    """POST /api/clients — create a new client (all fields)."""
    data = request.get_json(silent=True) or {}
    if not data.get("name", "").strip():
        return jsonify({"error": "Client name is required."}), 400
    try:
        record = cm.add_client(data)
        return jsonify(record), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.put("/api/clients/<int:client_id>")
def api_update_client(client_id: int):
    """PUT /api/clients/<id> — update an existing client."""
    data = request.get_json(silent=True) or {}
    record = cm.update_client(client_id, data)
    if record:
        return jsonify(record), 200
    return jsonify({"error": f"No client with id={client_id}."}), 404


@app.delete("/api/clients/<int:client_id>")
def api_delete_client(client_id: int):
    """DELETE /api/clients/<id>"""
    if cm.delete_client(client_id):
        return jsonify({"message": f"Client {client_id} deleted."}), 200
    return jsonify({"error": f"No client with id={client_id}."}), 404


@app.get("/api/clients/export.csv")
def api_export_clients_csv():
    """
    GET /api/clients/export.csv
    Returns a downloadable CSV with all registered clients.
    Excluded fields: revenue_password, legacy_phone.
    """
    EXCLUDED = {"revenue_password", "legacy_phone"}

    clients = cm.list_clients()          # list of dicts, already enriched
    if not clients:
        # Return an empty CSV with just headers if no clients yet
        all_keys = ["finflow_number", "id", "name", "civil_status", "pps_number",
                    "date_of_birth", "email", "mobile", "other_phone",
                    "address_line1", "address_line2", "address_line3",
                    "city_county", "eir_code", "bank_holder_name",
                    "bank_iban", "bank_bic", "paye_agent_name",
                    "paye_tain", "created_at"]
    else:
        all_keys = [k for k in clients[0].keys() if k not in EXCLUDED]

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=all_keys,
        extrasaction="ignore",
        lineterminator="\r\n",
    )
    writer.writeheader()
    for row in clients:
        writer.writerow({k: row.get(k, "") for k in all_keys})

    csv_bytes = buf.getvalue().encode("utf-8-sig")   # BOM for Excel compatibility
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=finflowai_clients.csv",
            "Content-Length": str(len(csv_bytes)),
        }
    )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"FinFlowAI server starting at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
