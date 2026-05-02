"""Notification + SMTP tests."""

from __future__ import annotations

from unittest import mock

import pytest

from barber_booking.notifications import (
    SmtpConfig,
    notify,
    send_email,
    smtp_config_from_env,
)

FULL_ENV = {
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "noreply@example.com",
    "SMTP_PASS": "secret",
    "SMTP_FROM": "from@example.com",
}


# ── smtp_config_from_env ──────────────────────────────────────────────


def test_smtp_config_returns_none_when_empty() -> None:
    assert smtp_config_from_env({}) is None


@pytest.mark.parametrize(
    "missing", ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"]
)
def test_smtp_config_returns_none_when_required_var_missing(missing: str) -> None:
    env = {k: v for k, v in FULL_ENV.items() if k != missing}
    assert smtp_config_from_env(env) is None


def test_smtp_config_full() -> None:
    cfg = smtp_config_from_env(FULL_ENV)
    assert cfg == SmtpConfig(
        host="smtp.example.com",
        port="587",
        user="noreply@example.com",
        password="secret",
        sender="from@example.com",
    )


def test_smtp_config_defaults_sender_to_user() -> None:
    env = {k: v for k, v in FULL_ENV.items() if k != "SMTP_FROM"}
    cfg = smtp_config_from_env(env)
    assert cfg is not None and cfg.sender == "noreply@example.com"


# ── send_email ────────────────────────────────────────────────────────


def _cfg() -> SmtpConfig:
    return SmtpConfig("smtp.example.com", "587", "u", "p", "from@example.com")


def test_send_email_returns_false_for_empty_recipient() -> None:
    assert send_email(_cfg(), "", "subj", "body") is False


def test_send_email_happy_path() -> None:
    with mock.patch("barber_booking.notifications.smtplib.SMTP") as smtp_cls:
        server = smtp_cls.return_value.__enter__.return_value
        ok = send_email(_cfg(), "to@example.com", "subj", "body")
    assert ok is True
    smtp_cls.assert_called_once_with("smtp.example.com", 587)
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("u", "p")
    server.sendmail.assert_called_once()
    args = server.sendmail.call_args.args
    assert args[0] == "from@example.com"
    assert args[1] == ["to@example.com"]
    assert "Subject: subj" in args[2]


def test_send_email_swallows_exception_returns_false() -> None:
    captured: list[str] = []
    with mock.patch(
        "barber_booking.notifications.smtplib.SMTP", side_effect=OSError("boom")
    ):
        ok = send_email(
            _cfg(), "to@example.com", "subj", "body", printer=captured.append
        )
    assert ok is False
    assert any("Email failed" in line for line in captured)


def test_send_email_non_numeric_port_returns_false() -> None:
    """Non-numeric ``SMTP_PORT`` is swallowed by the broad ``except Exception``
    in :func:`send_email`, matching the legacy implementation."""
    captured: list[str] = []
    cfg = SmtpConfig("smtp.example.com", "not-a-number", "u", "p", "f")
    ok = send_email(
        cfg, "to@example.com", "subj", "body", printer=captured.append
    )
    assert ok is False
    assert any("invalid literal for int" in line for line in captured)


# ── notify ────────────────────────────────────────────────────────────


def test_notify_prints_block_without_email() -> None:
    captured: list[str] = []
    notify(
        "barber",
        "Alice",
        "hello",
        email="",
        printer=captured.append,
        env={},
    )
    blob = "\n".join(captured)
    assert "[BARBER]" in blob
    assert "To: Alice" in blob
    assert "Message: hello" in blob
    assert "Email" not in blob.split("Message: hello", 1)[1]


def test_notify_skipped_when_smtp_not_configured() -> None:
    captured: list[str] = []
    notify(
        "client",
        "Carol",
        "msg",
        email="carol@example.com",
        printer=captured.append,
        env={},
    )
    assert any("SMTP not configured" in line for line in captured)


def test_notify_sends_email_when_configured() -> None:
    captured: list[str] = []
    with mock.patch("barber_booking.notifications.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__.return_value.sendmail.return_value = None
        notify(
            "client",
            "Carol",
            "msg",
            email="carol@example.com",
            printer=captured.append,
            env=FULL_ENV,
        )
    assert any("Email sent to: carol@example.com" in line for line in captured)


def test_notify_client_tag() -> None:
    captured: list[str] = []
    notify("client", "Dan", "x", printer=captured.append, env={})
    assert any("[CLIENT]" in line for line in captured)
