"""
Professional HTML email templates for the Barber Booking Agent.

Renders multipart-friendly (text + HTML) emails for booking confirmations,
reschedules, and cancellations. Pure standard library, no dependencies.
"""

from html import escape

BRAND = "Barber Booking Agent"
PRIMARY = "#1f2937"
ACCENT = "#0ea5e9"
MUTED = "#6b7280"
BG = "#f4f6f8"
CARD = "#ffffff"
BORDER = "#e5e7eb"

STATUS_STYLES = {
    "confirmed":   {"label": "Confirmed",   "color": "#047857", "bg": "#d1fae5"},
    "rescheduled": {"label": "Rescheduled", "color": "#b45309", "bg": "#fef3c7"},
    "cancelled":   {"label": "Cancelled",   "color": "#b91c1c", "bg": "#fee2e2"},
}

HEADLINES = {
    ("confirmed",   "client"): "Your appointment is confirmed",
    ("confirmed",   "barber"): "You have a new appointment",
    ("rescheduled", "client"): "Your appointment has been rescheduled",
    ("rescheduled", "barber"): "An appointment has been rescheduled",
    ("cancelled",   "client"): "Your appointment has been cancelled",
    ("cancelled",   "barber"): "An appointment has been cancelled",
}


def _row(label, value):
    return f"""
        <tr>
          <td style="padding:10px 0;color:{MUTED};font-size:14px;width:140px;vertical-align:top;">{escape(label)}</td>
          <td style="padding:10px 0;color:{PRIMARY};font-size:15px;font-weight:600;">{escape(value)}</td>
        </tr>"""


def render_booking_email(event, recipient_type, booking, previous=None):
    """Render (subject, text_body, html_body) for a booking event.

    event: 'confirmed' | 'rescheduled' | 'cancelled'
    recipient_type: 'client' | 'barber'
    booking: dict with keys barber, client, date, time, service, price, client_email
    previous: optional dict {'date': ..., 'time': ...} for reschedules
    """
    status = STATUS_STYLES[event]
    headline = HEADLINES[(event, recipient_type)]
    recipient_name = booking["client"] if recipient_type == "client" else booking["barber"]
    counterparty_label = "Barber" if recipient_type == "client" else "Client"
    counterparty_name = booking["barber"] if recipient_type == "client" else booking["client"]

    service = booking.get("service")
    price = booking.get("price", 0) or 0

    subject = f"[{BRAND}] {status['label']}: {booking['date']} at {booking['time']} with {booking['barber']}"

    rows = [_row(counterparty_label, counterparty_name)]
    if event == "rescheduled" and previous:
        rows.append(_row("Previous", f"{previous['date']} at {previous['time']}"))
        rows.append(_row("New Date", booking["date"]))
        rows.append(_row("New Time", booking["time"]))
    else:
        rows.append(_row("Date", booking["date"]))
        rows.append(_row("Time", booking["time"]))
    if service:
        rows.append(_row("Service", service))
        rows.append(_row("Price", f"${price:.2f}"))

    intro_map = {
        ("confirmed",   "client"): f"Hi {booking['client']}, your appointment is booked. We look forward to seeing you.",
        ("confirmed",   "barber"): f"Hi {booking['barber']}, a new appointment has been added to your calendar.",
        ("rescheduled", "client"): f"Hi {booking['client']}, your appointment has been moved to a new date and time.",
        ("rescheduled", "barber"): f"Hi {booking['barber']}, an appointment on your calendar has been rescheduled.",
        ("cancelled",   "client"): f"Hi {booking['client']}, your appointment has been cancelled. We hope to see you another time.",
        ("cancelled",   "barber"): f"Hi {booking['barber']}, an appointment has been cancelled and removed from your calendar.",
    }
    intro = intro_map[(event, recipient_type)]

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:{PRIMARY};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:{CARD};border:1px solid {BORDER};border-radius:12px;overflow:hidden;">
          <tr>
            <td style="background:{PRIMARY};padding:24px 32px;color:#ffffff;">
              <div style="font-size:13px;letter-spacing:1.5px;text-transform:uppercase;color:#9ca3af;">{escape(BRAND)}</div>
              <div style="font-size:22px;font-weight:700;margin-top:6px;">{escape(headline)}</div>
            </td>
          </tr>
          <tr>
            <td style="padding:28px 32px 8px 32px;">
              <span style="display:inline-block;padding:6px 12px;border-radius:999px;font-size:12px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;color:{status['color']};background:{status['bg']};">
                {escape(status['label'])}
              </span>
              <p style="margin:18px 0 0 0;font-size:15px;line-height:1.6;color:{PRIMARY};">{escape(intro)}</p>
            </td>
          </tr>
          <tr>
            <td style="padding:16px 32px 8px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {BORDER};border-bottom:1px solid {BORDER};">
                {''.join(rows)}
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 32px 32px 32px;">
              <p style="margin:0;font-size:14px;line-height:1.6;color:{MUTED};">
                If you have any questions, simply reply to this email and we will get back to you.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background:#fafafa;padding:18px 32px;border-top:1px solid {BORDER};text-align:center;">
              <div style="font-size:12px;color:{MUTED};">
                You're receiving this email because an appointment was {escape(event)} for {escape(recipient_name)}.
              </div>
              <div style="font-size:12px;color:{MUTED};margin-top:6px;">
                &copy; {escape(BRAND)}
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    text_lines = [
        f"{BRAND}",
        f"{headline}",
        "",
        f"Status: {status['label']}",
        intro,
        "",
        f"{counterparty_label}: {counterparty_name}",
    ]
    if event == "rescheduled" and previous:
        text_lines.append(f"Previous: {previous['date']} at {previous['time']}")
        text_lines.append(f"New Date: {booking['date']}")
        text_lines.append(f"New Time: {booking['time']}")
    else:
        text_lines.append(f"Date: {booking['date']}")
        text_lines.append(f"Time: {booking['time']}")
    if service:
        text_lines.append(f"Service: {service}")
        text_lines.append(f"Price: ${price:.2f}")
    text_lines += [
        "",
        "If you have any questions, simply reply to this email.",
        "",
        f"-- {BRAND}",
    ]
    text_body = "\n".join(text_lines)

    return subject, text_body, html_body
