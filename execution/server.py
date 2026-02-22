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

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

import user_manager as um

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


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(WEB_DIR, filename)


# ── API: Login ─────────────────────────────────────────────────────────────────

@app.post("/api/login")
def api_login():
    """
    POST /api/login
    Body: { "space": "...", "login": "...", "password": "..." }
    Returns 200 on success, 401 on invalid credentials, 400 on missing fields.
    """
    data = request.get_json(silent=True) or {}
    space    = data.get("space", "").strip()
    login    = data.get("login", "").strip()
    password = data.get("password", "").strip()

    if not all([space, login, password]):
        return jsonify({"error": "All fields (space, login, password) are required."}), 400

    if um.verify_user(space, login, password):
        return jsonify({"success": True, "message": f"Welcome, {login}!"}), 200
    else:
        return jsonify({"error": "Invalid space, login, or password."}), 401


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

    if not all([space, login, password]):
        return jsonify({"error": "All fields (space, login, password) are required."}), 400

    try:
        record = um.add_user(space, login, password)
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


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    print(f"FinFlowAI server starting at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
