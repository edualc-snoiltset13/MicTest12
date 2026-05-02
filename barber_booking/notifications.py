"""Console + SMTP notifications.

`smtp_config_from_env` is pure (env passed in). Side effects (network, print)
are confined to `send_email` and `notify`.
"""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import Callable, Mapping

__all__ = ["SmtpConfig", "smtp_config_from_env", "send_email", "notify"]


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: str
    user: str
    password: str
    sender: str


def smtp_config_from_env(env: Mapping[str, str]) -> SmtpConfig | None:
    host = env.get("SMTP_HOST")
    port = env.get("SMTP_PORT")
    user = env.get("SMTP_USER")
    password = env.get("SMTP_PASS")
    if not (host and port and user and password):
        return None
    sender = env.get("SMTP_FROM", user)
    return SmtpConfig(host=host, port=port, user=user, password=password, sender=sender)


def send_email(
    cfg: SmtpConfig,
    to_addr: str,
    subject: str,
    body: str,
    *,
    printer: Callable[[str], None] = print,
) -> bool:
    if not to_addr:
        return False
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = cfg.sender
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(cfg.host, int(cfg.port)) as server:
            server.starttls()
            server.login(cfg.user, cfg.password)
            server.sendmail(cfg.sender, [to_addr], msg.as_string())
        return True
    except Exception as e:
        printer(f"  (Email failed: {e})")
        return False


def notify(
    recipient_type: str,
    name: str,
    message: str,
    email: str = "",
    *,
    printer: Callable[[str], None] = print,
    env: Mapping[str, str] | None = None,
) -> None:
    tag = "BARBER" if recipient_type == "barber" else "CLIENT"
    printer(f"\n--- Notification [{tag}] ---")
    printer(f"To: {name}")
    printer(f"Message: {message}")
    if email:
        cfg = smtp_config_from_env(env if env is not None else os.environ)
        sent = False
        if cfg is not None:
            sent = send_email(
                cfg, email, f"Barber Booking - {tag}", message, printer=printer
            )
        if sent:
            printer(f"Email sent to: {email}")
        else:
            printer("Email: (skipped - SMTP not configured or send failed)")
    printer("----------------------------\n")
