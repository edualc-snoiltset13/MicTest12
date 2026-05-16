"""SQLite-backed demo account store for the PayPal login UI recreation.

This module is intentionally educational. It demonstrates:
  * A small users table in SQLite.
  * Password hashing with scrypt + a per-user random salt.
  * Constant-time password verification.
  * Parameterized queries (no string interpolation into SQL).
  * A local-only (127.0.0.1) JSON HTTP server that pairs with
    paypal-login.html.

It does NOT collect, transmit, or store real PayPal credentials. The
companion HTML file is a UI mock-up and the only network destination is
the loopback interface on the same machine.

CLI:
    python paypal_demo_db.py init
    python paypal_demo_db.py register <email> <password>
    python paypal_demo_db.py login <email> <password>
    python paypal_demo_db.py list
    python paypal_demo_db.py delete <email>
    python paypal_demo_db.py serve [--port 8000]

Options:
    --db PATH    Override the default database path (paypal_demo.db).
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

DEFAULT_DB = Path(__file__).resolve().parent / "paypal_demo.db"

# scrypt parameters — RFC 7914 / OWASP recommended starting point.
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    salt        BLOB    NOT NULL,
    pw_hash     BLOB    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Return (salt, hash). Generates a fresh salt if none is supplied."""
    if salt is None:
        salt = secrets.token_bytes(SALT_BYTES)
    pw_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=KEY_BYTES,
    )
    return salt, pw_hash


def verify_password(password: str, salt: bytes, expected_hash: bytes) -> bool:
    _, candidate = hash_password(password, salt=salt)
    return hmac.compare_digest(candidate, expected_hash)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def connect(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DEFAULT_DB) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def register_user(email: str, password: str, db_path: Path = DEFAULT_DB) -> int:
    email = email.strip()
    if not email or "@" not in email:
        raise ValueError("email must contain '@'")
    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")
    salt, pw_hash = hash_password(password)
    with connect(db_path) as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (email, salt, pw_hash) VALUES (?, ?, ?)",
                (email, salt, pw_hash),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"account already exists: {email}") from exc
        return int(cur.lastrowid)


def authenticate(email: str, password: str, db_path: Path = DEFAULT_DB) -> bool:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT salt, pw_hash FROM users WHERE email = ?",
            (email.strip(),),
        ).fetchone()
    if row is None:
        # Run the hash anyway so timing doesn't reveal account existence.
        hash_password(password)
        return False
    return verify_password(password, row["salt"], row["pw_hash"])


def list_users(db_path: Path = DEFAULT_DB) -> list[sqlite3.Row]:
    with connect(db_path) as conn:
        return list(conn.execute(
            "SELECT id, email, created_at FROM users ORDER BY id"
        ))


def delete_user(email: str, db_path: Path = DEFAULT_DB) -> bool:
    with connect(db_path) as conn:
        cur = conn.execute("DELETE FROM users WHERE email = ?", (email.strip(),))
        return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Local HTTP server (loopback only)
# ---------------------------------------------------------------------------

class DemoHandler(BaseHTTPRequestHandler):
    db_path: Path = DEFAULT_DB
    static_root: Path = Path(__file__).resolve().parent

    def log_message(self, fmt, *args):
        sys.stderr.write("[demo] " + fmt % args + "\n")

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > 4096:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}

    def do_GET(self):  # noqa: N802 (BaseHTTPRequestHandler API)
        path = "paypal-login.html" if self.path in ("/", "/index", "/login") else self.path.lstrip("/")
        target = (self.static_root / path).resolve()
        if not str(target).startswith(str(self.static_root)) or not target.is_file():
            self.send_error(404, "Not found")
            return
        data = target.read_bytes()
        ctype = "text/html; charset=utf-8" if target.suffix == ".html" else "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):  # noqa: N802
        body = self._read_json()
        email = (body.get("email") or "").strip()
        password = body.get("password") or ""

        if self.path == "/api/register":
            try:
                user_id = register_user(email, password, db_path=self.db_path)
            except ValueError as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
                return
            self._send_json(201, {"ok": True, "id": user_id})
            return

        if self.path == "/api/login":
            ok = authenticate(email, password, db_path=self.db_path)
            status = 200 if ok else 401
            self._send_json(status, {"ok": ok})
            return

        self.send_error(404, "Not found")


def serve(host: str = "127.0.0.1", port: int = 8000, db_path: Path = DEFAULT_DB) -> None:
    init_db(db_path)
    DemoHandler.db_path = db_path
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("refusing to bind to non-loopback host for safety")
    httpd = HTTPServer((host, port), DemoHandler)
    print(f"Demo server (LOCAL ONLY) on http://{host}:{port}")
    print("This server stores only locally-created demo accounts.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        httpd.server_close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create the database schema")

    reg = sub.add_parser("register", help="Create a new demo account")
    reg.add_argument("email")
    reg.add_argument("password")

    lg = sub.add_parser("login", help="Verify credentials for an account")
    lg.add_argument("email")
    lg.add_argument("password")

    sub.add_parser("list", help="List all demo accounts")

    dl = sub.add_parser("delete", help="Delete a demo account")
    dl.add_argument("email")

    srv = sub.add_parser("serve", help="Run the local demo HTTP server")
    srv.add_argument("--port", type=int, default=8000)
    srv.add_argument("--host", default="127.0.0.1")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    db_path = args.db

    if args.cmd == "init":
        init_db(db_path)
        print(f"Initialized {db_path}")
        return 0

    if args.cmd == "register":
        init_db(db_path)
        try:
            user_id = register_user(args.email, args.password, db_path=db_path)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Registered #{user_id} {args.email}")
        return 0

    if args.cmd == "login":
        init_db(db_path)
        ok = authenticate(args.email, args.password, db_path=db_path)
        print("OK" if ok else "FAIL")
        return 0 if ok else 1

    if args.cmd == "list":
        init_db(db_path)
        rows = list_users(db_path=db_path)
        if not rows:
            print("(no accounts)")
            return 0
        for r in rows:
            print(f"{r['id']:>4}  {r['email']:<40}  {r['created_at']}")
        return 0

    if args.cmd == "delete":
        init_db(db_path)
        ok = delete_user(args.email, db_path=db_path)
        print("deleted" if ok else "not found")
        return 0 if ok else 1

    if args.cmd == "serve":
        serve(host=args.host, port=args.port, db_path=db_path)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
