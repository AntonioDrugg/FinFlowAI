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
import space_manager        as sm
import refund_processor     as rp
import space_settings_manager as ssm


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


@app.route("/spaces-management.html")
def spaces_management_page():
    return send_from_directory(WEB_DIR, "spaces-management.html")


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
    Returns 201 on success, 409 on duplicate, 400 on missing fields, 404 if space not registered.
    """
    data = request.get_json(silent=True) or {}
    space    = data.get("space", "").strip()
    login    = data.get("login", "").strip()
    password = data.get("password", "").strip()
    name     = data.get("name", "").strip()

    if not all([space, login, password]):
        return jsonify({"error": "All fields (space, login, password) are required."}), 400

    # Enforce space registration
    if not sm.space_exists(space):
        return jsonify({
            "error": f"Space '{space}' is not registered. Register the space first in Space Setup."
        }), 404

    try:
        record = um.add_user(space, login, password, name)
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


# ── API: Spaces ───────────────────────────────────────────────────────────────
# A space must exist here before users or clients can be created in it.

@app.get("/api/spaces")
def api_list_spaces():
    """GET /api/spaces -- list all registered spaces."""
    return jsonify(sm.list_spaces()), 200


@app.post("/api/spaces")
def api_create_space():
    """
    POST /api/spaces
    Body: { "name": "acme-tax", "code": "AT" }
    Returns 201 on success, 409 on duplicate, 400 on validation error.
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    code = data.get("code", "").strip()
    if not name or not code:
        return jsonify({"error": "Both 'name' and 'code' are required."}), 400
    try:
        space = sm.create_space(name, code)
        return jsonify(space), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@app.get("/api/spaces/<space_name>")
def api_get_space(space_name: str):
    """GET /api/spaces/<name> -- get a single space by name."""
    space = sm.get_space(space_name)
    if space:
        return jsonify(space), 200
    return jsonify({"error": f"Space '{space_name}' is not registered."}), 404


# ── API: Clients ───────────────────────────────────────────────────────────────
# All client endpoints are scoped by space.  The caller always passes
# ?space=<name>  (GET/DELETE) or { "space": "<name>" } in the JSON body
# (POST / PUT) so that each space's data is fully isolated.

@app.get("/api/clients")
def api_list_clients():
    """GET /api/clients?space=<name> — return all clients for the given space."""
    space = request.args.get("space", "").strip()
    return jsonify(cm.list_clients(space)), 200


@app.get("/api/clients/<int:client_id>")
def api_get_client(client_id: int):
    """GET /api/clients/<id>?space=<name> — return a single client."""
    space = request.args.get("space", "").strip()
    record = cm.get_client(client_id, space)
    if record:
        return jsonify(record), 200
    return jsonify({"error": f"No client with id={client_id}."}), 404


@app.post("/api/clients")
def api_add_client():
    """POST /api/clients -- create a new client. Body must include 'space' and 'name'."""
    data  = request.get_json(silent=True) or {}
    space = data.pop("space", "").strip()
    if not space:
        return jsonify({"error": "'space' is required."}), 400
    if not data.get("name", "").strip():
        return jsonify({"error": "Client name is required."}), 400

    # Enforce space registration
    if not sm.space_exists(space):
        return jsonify({
            "error": f"Space '{space}' is not registered. Register the space first in Space Setup."
        }), 404

    try:
        record = cm.add_client(data, space)
        return jsonify(record), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.put("/api/clients/<int:client_id>")
def api_update_client(client_id: int):
    """PUT /api/clients/<id> — update a client. Body must include 'space'."""
    data  = request.get_json(silent=True) or {}
    space = data.pop("space", "").strip()
    record = cm.update_client(client_id, data, space)
    if record:
        return jsonify(record), 200
    return jsonify({"error": f"No client with id={client_id} in space '{space}'."}), 404


@app.delete("/api/clients/<int:client_id>")
def api_delete_client(client_id: int):
    """DELETE /api/clients/<id>?space=<name>"""
    space = request.args.get("space", "").strip()
    if cm.delete_client(client_id, space):
        return jsonify({"message": f"Client {client_id} deleted."}), 200
    return jsonify({"error": f"No client with id={client_id} in space '{space}'."}), 404


@app.get("/api/clients/export.csv")
def api_export_clients_csv():
    """
    GET /api/clients/export.csv?space=<name>
    Returns a downloadable CSV for the given space.
    Excluded fields: revenue_password, legacy_phone, space.
    """
    EXCLUDED = {"revenue_password", "legacy_phone", "space"}
    space = request.args.get("space", "").strip()

    clients = cm.list_clients(space)
    if not clients:
        all_keys = ["finflow_number", "id", "name", "civil_status", "pps_number",
                    "date_of_birth", "email", "mobile", "other_phone",
                    "address_line1", "address_line2", "address_line3",
                    "city_county", "eir_code", "bank_holder_name",
                    "bank_iban", "bank_bic"]
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
    prefix = cm.space_code(space)
    filename = f"finflowai_{prefix.lower()}_clients.csv"
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(len(csv_bytes)),
        }
    )


@app.post("/api/clients/import.csv")
def api_import_clients_csv():
    """
    POST /api/clients/import.csv?space=<name>
    Accepts a multipart file upload (field name: 'file').
    Imports every row that has at least a 'name' column.
    Auto-assigns FinFlow numbers — no existing clients are deleted.
    Returns { added, skipped, errors: [...] }
    """
    space = request.args.get("space", "").strip()
    if not space:
        return jsonify({"error": "'space' query parameter is required."}), 400

    if not sm.space_exists(space):
        return jsonify({
            "error": f"Space '{space}' is not registered."
        }), 404

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Use field name 'file'."}), 400

    uploaded = request.files["file"]
    if not uploaded.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are accepted."}), 400

    added   = 0
    skipped = 0
    errors  = []

    try:
        text    = uploaded.stream.read().decode("utf-8-sig")   # handle BOM
        reader  = csv.DictReader(io.StringIO(text))
        valid_fields = set(cm.CLIENT_FIELDS)

        for i, row in enumerate(reader, start=2):          # row 1 = header
            # strip keys & values
            row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
            name = row.get("name", "").strip()

            if not name:
                skipped += 1
                continue

            # Keep only fields the client table knows about
            data = {k: v for k, v in row.items() if k in valid_fields}

            try:
                cm.add_client(data, space)
                added += 1
            except Exception as e:
                errors.append({"row": i, "name": name, "error": str(e)})

    except Exception as e:
        return jsonify({"error": f"Could not parse CSV: {e}"}), 400

    return jsonify({"added": added, "skipped": skipped, "errors": errors}), 200


# ── Processes ─────────────────────────────────────────────────────────────────

@app.post("/api/processes/refunds")
def api_run_refunds():
    """
    POST /api/processes/refunds
    Body: { "space": "...", "client_ids": [1, 2, 3] }
    Runs the refund check sequentially for each client_id in order.
    Returns: { "results": [ { ...per-client result... }, ... ] }
    """
    data       = request.get_json(silent=True) or {}
    space      = data.get("space", "").strip()
    client_ids = data.get("client_ids", [])

    if not space:
        return jsonify({"error": "'space' is required."}), 400
    if not isinstance(client_ids, list) or len(client_ids) == 0:
        return jsonify({"error": "'client_ids' must be a non-empty list."}), 400
    if not sm.space_exists(space):
        return jsonify({"error": f"Space '{space}' is not registered."}), 404

    try:
        client_ids = [int(i) for i in client_ids]
    except (TypeError, ValueError):
        return jsonify({"error": "All client_ids must be integers."}), 400

    results = rp.run_refunds(client_ids, space)
    return jsonify({"results": results}), 200



# ── Space Settings ─────────────────────────────────────────────────────────────

@app.get("/api/spaces/<name>/settings")
def api_get_space_settings(name: str):
    """GET /api/spaces/<name>/settings — return TAIN + ROS ID for the space."""
    name = name.strip().lower()
    if not sm.space_exists(name):
        return jsonify({"error": f"Space '{name}' not found."}), 404
    return jsonify(ssm.get_settings(name)), 200


@app.put("/api/spaces/<name>/settings")
def api_update_space_settings(name: str):
    """
    PUT /api/spaces/<name>/settings
    Body: { "tain": "...", "ros_id": "..." }  (either or both)
    """
    name = name.strip().lower()
    if not sm.space_exists(name):
        return jsonify({"error": f"Space '{name}' not found."}), 404

    data   = request.get_json(silent=True) or {}
    tain   = data.get("tain")
    ros_id = data.get("ros_id")

    if tain is None and ros_id is None:
        return jsonify({"error": "Provide at least 'tain' or 'ros_id'."}), 400

    try:
        record = ssm.upsert_settings(name, tain=tain, ros_id=ros_id)
        return jsonify(record), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":

    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"FinFlowAI server starting at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
