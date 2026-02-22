# Directive: Password Module

## Goal
Manage user credentials organised by **Spaces**. Each Space is an independent
authentication domain. Credentials are stored in a local SQLite database with
a uniqueness constraint on the combination of `(space, login, password)`.

## Core Rules
1. **Spaces are independent** — the same login can exist in different spaces without conflict.
2. **Triple uniqueness** — the exact combination of `(space, login, password)` must be unique.
   - Duplicate triples are rejected at both the DB and application layer.
3. **Passwords are hashed** — stored as `SHA-256(password + APP_SECRET)` for deterministic,
   secure comparison without storing plain text.

## Database
- **Engine:** SQLite
- **File:** `.tmp/finflowai.db`
- **Table:** `users`

```sql
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    space         TEXT    NOT NULL,
    login         TEXT    NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(space, login, password_hash)
);
```

## Scripts

| Script | Purpose |
|--------|---------|
| `execution/setup_db.py` | Creates the database and table (idempotent) |
| `execution/user_manager.py` | Add, list, delete, and verify credentials |
| `execution/server.py` | Flask web server — serves UI + REST API |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/login` | Verify credentials; returns success or error |
| `GET`  | `/api/users` | List all credential records (admin) |
| `POST` | `/api/users` | Add a new (space, login, password) record |
| `DELETE` | `/api/users/<id>` | Remove a record by ID |

## Setup & Run

```bash
# 1. Create the database
python execution/setup_db.py

# 2. Add a test user
python execution/user_manager.py add --space "acme" --login "alice" --password "secret"

# 3. Start the server
python execution/server.py
# → http://localhost:5000
```

## Edge Cases
- If the DB file is missing, `setup_db.py` creates it automatically.
- Duplicate triple → `409 Conflict` from the API, shown as an error on the UI.
- Empty fields on login → `400 Bad Request`.
- All spaces are case-insensitive (lowercased before storage and comparison).

## Update Log
- 2026-02-22: Directive created
