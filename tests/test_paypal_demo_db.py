"""Tests for paypal_demo_db.py — the demo SQLite account store."""

import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import paypal_demo_db as demo  # noqa: E402


class HashingTests(unittest.TestCase):
    def test_hash_returns_distinct_salts(self):
        s1, h1 = demo.hash_password("hunter22-demo")
        s2, h2 = demo.hash_password("hunter22-demo")
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(h1, h2)
        self.assertEqual(len(s1), demo.SALT_BYTES)
        self.assertEqual(len(h1), demo.KEY_BYTES)

    def test_verify_password_roundtrip(self):
        salt, pw_hash = demo.hash_password("hunter22-demo")
        self.assertTrue(demo.verify_password("hunter22-demo", salt, pw_hash))
        self.assertFalse(demo.verify_password("wrong-password", salt, pw_hash))


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = Path(self._tmp.name) / "test.db"
        demo.init_db(self.db)

    def tearDown(self):
        self._tmp.cleanup()

    def test_register_and_authenticate(self):
        uid = demo.register_user("alice@example.com", "correct-horse", db_path=self.db)
        self.assertGreater(uid, 0)
        self.assertTrue(demo.authenticate("alice@example.com", "correct-horse", db_path=self.db))
        self.assertFalse(demo.authenticate("alice@example.com", "nope", db_path=self.db))

    def test_email_uniqueness_is_case_insensitive(self):
        demo.register_user("Bob@Example.com", "password1", db_path=self.db)
        with self.assertRaises(ValueError):
            demo.register_user("bob@example.com", "password2", db_path=self.db)
        # Original credentials still work, and lookup is case-insensitive.
        self.assertTrue(demo.authenticate("BOB@example.com", "password1", db_path=self.db))

    def test_register_rejects_short_password(self):
        with self.assertRaises(ValueError):
            demo.register_user("c@example.com", "short", db_path=self.db)

    def test_register_rejects_invalid_email(self):
        with self.assertRaises(ValueError):
            demo.register_user("not-an-email", "longenough", db_path=self.db)

    def test_unknown_user_does_not_authenticate(self):
        self.assertFalse(demo.authenticate("ghost@example.com", "whatever", db_path=self.db))

    def test_list_and_delete(self):
        demo.register_user("a@example.com", "password1", db_path=self.db)
        demo.register_user("b@example.com", "password2", db_path=self.db)
        emails = [r["email"] for r in demo.list_users(db_path=self.db)]
        self.assertEqual(sorted(emails), ["a@example.com", "b@example.com"])
        self.assertTrue(demo.delete_user("a@example.com", db_path=self.db))
        self.assertFalse(demo.delete_user("a@example.com", db_path=self.db))
        emails = [r["email"] for r in demo.list_users(db_path=self.db)]
        self.assertEqual(emails, ["b@example.com"])


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.db = Path(self._tmp.name) / "cli.db"

    def tearDown(self):
        self._tmp.cleanup()

    def test_register_then_login_via_main(self):
        self.assertEqual(demo.main(["--db", str(self.db), "register", "u@x.com", "password1"]), 0)
        self.assertEqual(demo.main(["--db", str(self.db), "login", "u@x.com", "password1"]), 0)
        self.assertEqual(demo.main(["--db", str(self.db), "login", "u@x.com", "wrong-password"]), 1)


class ServerTests(unittest.TestCase):
    """End-to-end test against the loopback HTTP server."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db = Path(cls._tmp.name) / "srv.db"
        demo.init_db(cls.db)
        demo.DemoHandler.db_path = cls.db
        # Bind to an ephemeral port and capture it.
        cls.httpd = HTTPServer(("127.0.0.1", 0), demo.DemoHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        # Give the loop a moment to start.
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls._tmp.cleanup()

    def _post(self, path, payload):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    def test_register_then_login(self):
        status, body = self._post("/api/register", {"email": "srv@x.com", "password": "password1"})
        self.assertEqual(status, 201)
        self.assertTrue(body["ok"])

        status, body = self._post("/api/login", {"email": "srv@x.com", "password": "password1"})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

        status, body = self._post("/api/login", {"email": "srv@x.com", "password": "wrong"})
        self.assertEqual(status, 401)
        self.assertFalse(body["ok"])

    def test_register_short_password_is_rejected(self):
        status, body = self._post("/api/register", {"email": "short@x.com", "password": "x"})
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])

    def test_serves_static_html(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/", timeout=2) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
        self.assertIn("Log in to your account", content)
        self.assertIn("educational purposes", content)

    def test_rejects_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            demo.serve(host="0.0.0.0", port=0)


if __name__ == "__main__":
    unittest.main()
