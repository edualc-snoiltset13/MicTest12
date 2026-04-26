"""Unit tests for barber_booking_agent.

Stdlib-only: run with `python -m unittest discover -s tests`.
"""

import io
import json
import os
import smtplib
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

# Make the project root importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import barber_booking_agent as bba  # noqa: E402


def _sample_data():
    return {
        "barbers": {
            "Alice": {
                "slots": ["09:00", "10:00"],
                "services": {"Haircut": 25.0},
                "email": "alice@example.com",
            },
            "Bob": {"slots": ["11:00"], "services": {}, "email": ""},
        },
        "bookings": [
            {
                "barber": "Alice",
                "client": "Carol",
                "client_email": "carol@example.com",
                "date": "2099-01-01",
                "time": "09:00",
                "service": "Haircut",
                "price": 25.0,
                "booked_at": "2099-01-01T08:00:00",
            }
        ],
    }


class PersistenceTests(unittest.TestCase):
    """load_bookings / save_bookings."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = Path(self._cwd) / "_tmp_test_persistence"
        self._tmp.mkdir(exist_ok=True)
        os.chdir(self._tmp)

    def tearDown(self):
        os.chdir(self._cwd)
        for p in self._tmp.iterdir():
            p.unlink()
        self._tmp.rmdir()

    def test_missing_file_returns_skeleton(self):
        self.assertFalse(Path(bba.DATA_FILE).exists())
        data = bba.load_bookings()
        self.assertEqual(data, {"barbers": {}, "bookings": []})

    def test_round_trip_preserves_all_fields(self):
        original = _sample_data()
        bba.save_bookings(original)
        loaded = bba.load_bookings()
        self.assertEqual(loaded, original)

    def test_save_writes_indented_json(self):
        bba.save_bookings({"barbers": {}, "bookings": []})
        text = Path(bba.DATA_FILE).read_text()
        # indent=2 means at least one newline + leading spaces
        self.assertIn("\n  ", text)


class SlotLogicTests(unittest.TestCase):
    """_is_slot_taken."""

    def setUp(self):
        self.data = _sample_data()

    def test_taken_when_exact_match(self):
        self.assertTrue(bba._is_slot_taken(self.data, "Alice", "2099-01-01", "09:00"))

    def test_free_when_different_time(self):
        self.assertFalse(bba._is_slot_taken(self.data, "Alice", "2099-01-01", "10:00"))

    def test_free_when_different_date(self):
        self.assertFalse(bba._is_slot_taken(self.data, "Alice", "2099-01-02", "09:00"))

    def test_free_when_different_barber(self):
        self.assertFalse(bba._is_slot_taken(self.data, "Bob", "2099-01-01", "09:00"))

    def test_free_when_no_bookings(self):
        empty = {"barbers": {}, "bookings": []}
        self.assertFalse(bba._is_slot_taken(empty, "Alice", "2099-01-01", "09:00"))


class BarberEmailTests(unittest.TestCase):
    def setUp(self):
        self.data = _sample_data()

    def test_returns_email_when_present(self):
        self.assertEqual(bba._barber_email(self.data, "Alice"), "alice@example.com")

    def test_returns_empty_when_not_set(self):
        self.assertEqual(bba._barber_email(self.data, "Bob"), "")

    def test_returns_empty_when_unknown(self):
        self.assertEqual(bba._barber_email(self.data, "Nobody"), "")


class EmailNotificationTests(unittest.TestCase):
    """send_email_notification."""

    SMTP_ENV = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "user@example.com",
        "SMTP_PASS": "pw",
    }

    def test_returns_false_when_env_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(
                bba.send_email_notification("to@example.com", "subj", "body")
            )

    def test_returns_false_when_recipient_missing(self):
        with mock.patch.dict(os.environ, self.SMTP_ENV, clear=True):
            self.assertFalse(bba.send_email_notification("", "subj", "body"))

    def test_smtp_called_when_env_complete(self):
        with mock.patch.dict(os.environ, self.SMTP_ENV, clear=True):
            with mock.patch.object(smtplib, "SMTP") as smtp_cls:
                ok = bba.send_email_notification("to@example.com", "subj", "body")
        self.assertTrue(ok)
        smtp_cls.assert_called_once_with("smtp.example.com", 587)
        instance = smtp_cls.return_value.__enter__.return_value
        instance.starttls.assert_called_once()
        instance.login.assert_called_once_with("user@example.com", "pw")
        instance.sendmail.assert_called_once()
        sender, recipients, raw = instance.sendmail.call_args[0]
        self.assertEqual(sender, "user@example.com")
        self.assertEqual(recipients, ["to@example.com"])
        self.assertIn("Subject: subj", raw)
        self.assertIn("body", raw)

    def test_smtp_from_overrides_user_as_sender(self):
        env = {**self.SMTP_ENV, "SMTP_FROM": "noreply@example.com"}
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(smtplib, "SMTP") as smtp_cls:
                bba.send_email_notification("to@example.com", "s", "b")
        instance = smtp_cls.return_value.__enter__.return_value
        sender, _, raw = instance.sendmail.call_args[0]
        self.assertEqual(sender, "noreply@example.com")
        self.assertIn("From: noreply@example.com", raw)

    def test_returns_false_on_smtp_exception(self):
        with mock.patch.dict(os.environ, self.SMTP_ENV, clear=True):
            with mock.patch.object(smtplib, "SMTP", side_effect=OSError("boom")):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    ok = bba.send_email_notification("to@example.com", "s", "b")
        self.assertFalse(ok)
        self.assertIn("Email failed", buf.getvalue())


class NotifyTests(unittest.TestCase):
    """notify() console output."""

    def test_prints_barber_tag(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            bba.notify("barber", "Alice", "hello")
        self.assertIn("[BARBER]", buf.getvalue())
        self.assertIn("To: Alice", buf.getvalue())
        self.assertIn("Message: hello", buf.getvalue())

    def test_prints_client_tag_for_anything_else(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            bba.notify("client", "Carol", "hi")
        self.assertIn("[CLIENT]", buf.getvalue())

    def test_skips_email_when_no_address(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            bba.notify("client", "Carol", "hi", email=None)
        # no email skipped/sent line should appear
        self.assertNotIn("Email", buf.getvalue())


class ViewBookingsTests(unittest.TestCase):
    """view_bookings partitioning and formatting."""

    def test_empty_bookings_message(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            bba.view_bookings({"barbers": {}, "bookings": []})
        self.assertIn("No bookings yet.", buf.getvalue())

    def test_partitions_upcoming_and_past(self):
        data = {
            "barbers": {},
            "bookings": [
                {
                    "barber": "Alice",
                    "client": "Past",
                    "date": "1999-01-01",
                    "time": "09:00",
                    "service": None,
                    "price": 0,
                },
                {
                    "barber": "Alice",
                    "client": "Future",
                    "date": "2999-01-01",
                    "time": "09:00",
                    "service": "Haircut",
                    "price": 25.0,
                },
            ],
        }
        buf = io.StringIO()
        with redirect_stdout(buf):
            bba.view_bookings(data)
        out = buf.getvalue()
        self.assertIn("Upcoming:", out)
        self.assertIn("Past:", out)
        # Future booking shows service tag, past one does not.
        self.assertIn("[Haircut $25.00]", out)
        self.assertIn("Future with Alice", out)
        self.assertIn("Past with Alice", out)


class SearchBookingsTests(unittest.TestCase):
    """search_bookings input/output."""

    def _run(self, data, term):
        buf = io.StringIO()
        with mock.patch("builtins.input", return_value=term):
            with redirect_stdout(buf):
                bba.search_bookings(data)
        return buf.getvalue()

    def test_match_by_barber_case_insensitive(self):
        out = self._run(_sample_data(), "alice")
        self.assertIn("Found 1 booking(s):", out)
        self.assertIn("Carol with Alice", out)

    def test_match_by_client_partial(self):
        out = self._run(_sample_data(), "car")
        self.assertIn("Found 1 booking(s):", out)

    def test_no_matches(self):
        out = self._run(_sample_data(), "zzz")
        self.assertIn("No bookings found matching 'zzz'", out)

    def test_empty_term(self):
        out = self._run(_sample_data(), "   ")
        self.assertIn("Search term cannot be empty.", out)


class RegisterBarberTests(unittest.TestCase):
    """register_barber: end-to-end with mocked input/save."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = Path(self._cwd) / "_tmp_register"
        self._tmp.mkdir(exist_ok=True)
        os.chdir(self._tmp)

    def tearDown(self):
        os.chdir(self._cwd)
        for p in self._tmp.iterdir():
            p.unlink()
        self._tmp.rmdir()

    def test_registers_with_slots_and_services(self):
        data = {"barbers": {}, "bookings": []}
        inputs = iter(
            [
                "Alice",        # name
                "alice@x.com",  # email
                "09:00",        # slot
                "10:00",        # slot
                "done",
                "Haircut",      # service name
                "25.00",        # price
                "done",
            ]
        )
        with mock.patch("builtins.input", lambda *_a, **_kw: next(inputs)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                bba.register_barber(data)
        self.assertIn("Alice", data["barbers"])
        self.assertEqual(data["barbers"]["Alice"]["slots"], ["09:00", "10:00"])
        self.assertEqual(data["barbers"]["Alice"]["services"], {"Haircut": 25.0})
        self.assertEqual(data["barbers"]["Alice"]["email"], "alice@x.com")
        # Persistence side-effect: bookings.json should have been written.
        self.assertTrue(Path(bba.DATA_FILE).exists())
        on_disk = json.loads(Path(bba.DATA_FILE).read_text())
        self.assertIn("Alice", on_disk["barbers"])

    def test_rejects_empty_name(self):
        data = {"barbers": {}, "bookings": []}
        with mock.patch("builtins.input", return_value=""):
            buf = io.StringIO()
            with redirect_stdout(buf):
                bba.register_barber(data)
        self.assertEqual(data["barbers"], {})

    def test_rejects_duplicate(self):
        data = _sample_data()
        with mock.patch("builtins.input", return_value="Alice"):
            buf = io.StringIO()
            with redirect_stdout(buf):
                bba.register_barber(data)
        self.assertIn("already registered", buf.getvalue())

    def test_invalid_slot_format_skipped(self):
        data = {"barbers": {}, "bookings": []}
        inputs = iter(
            [
                "Alice", "", "9am", "09:00", "done", "done",  # bad slot then good slot
            ]
        )
        with mock.patch("builtins.input", lambda *_a, **_kw: next(inputs)):
            buf = io.StringIO()
            with redirect_stdout(buf):
                bba.register_barber(data)
        self.assertEqual(data["barbers"]["Alice"]["slots"], ["09:00"])


if __name__ == "__main__":
    unittest.main()
