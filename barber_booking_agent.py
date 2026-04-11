"""
Barber Booking Agent
A simple Python agent that manages barber appointment bookings,
maintains a calendar, and notifies both the barber and the client.

Features:
  - Register barbers with time slots and services/pricing
  - Book, reschedule, cancel appointments
  - Search bookings by barber or client name
  - Email notifications (when SMTP is configured via environment variables)
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

DATA_FILE = "bookings.json"


# ── Persistence ────────────────────────────────────────────────────


def load_bookings():
    """Load bookings from the JSON data file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"barbers": {}, "bookings": []}


def save_bookings(data):
    """Persist bookings to the JSON data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Notifications ──────────────────────────────────────────────────


def send_email_notification(to_addr, subject, body):
    """Send an email notification using SMTP settings from env vars.

    Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
    Optional: SMTP_FROM (defaults to SMTP_USER)
    """
    host = os.environ.get("SMTP_HOST")
    port = os.environ.get("SMTP_PORT")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    sender = os.environ.get("SMTP_FROM", user)

    if not all([host, port, user, password, to_addr]):
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_addr

    try:
        with smtplib.SMTP(host, int(port)) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, [to_addr], msg.as_string())
        return True
    except Exception as e:
        print(f"  (Email failed: {e})")
        return False


def notify(recipient_type, name, message, email=None):
    """Print a console notification and optionally send an email."""
    tag = "BARBER" if recipient_type == "barber" else "CLIENT"
    print(f"\n--- Notification [{tag}] ---")
    print(f"To: {name}")
    print(f"Message: {message}")
    if email:
        sent = send_email_notification(email, f"Barber Booking - {tag}", message)
        if sent:
            print(f"Email sent to: {email}")
        else:
            print(f"Email: (skipped - SMTP not configured or send failed)")
    print("----------------------------\n")


# ── Helper: get barber email ───────────────────────────────────────


def _barber_email(data, barber_name):
    return data["barbers"].get(barber_name, {}).get("email", "")


# ── Barber management ──────────────────────────────────────────────


def register_barber(data):
    """Register a new barber with available time slots and services."""
    print("\n== Register a Barber ==")
    name = input("Barber name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    if name in data["barbers"]:
        print(f"Barber '{name}' is already registered.")
        return

    email = input("Barber email (optional, press Enter to skip): ").strip()

    # Time slots
    print("Enter available time slots (24-hr format, e.g. 09:00).")
    print("Type 'done' when finished.")
    slots = []
    while True:
        slot = input("  Slot: ").strip()
        if slot.lower() == "done":
            break
        try:
            datetime.strptime(slot, "%H:%M")
            slots.append(slot)
        except ValueError:
            print("  Invalid format. Use HH:MM (e.g. 09:00).")

    # Services & pricing
    print("Enter services with prices (e.g. Haircut, then 25.00).")
    print("Type 'done' when finished.")
    services = {}
    while True:
        entry = input("  Service name: ").strip()
        if entry.lower() == "done":
            break
        if not entry:
            continue
        price_str = input(f"  Price for '{entry}': ").strip()
        try:
            price = round(float(price_str), 2)
            services[entry] = price
        except ValueError:
            print("  Invalid price. Skipping this service.")

    data["barbers"][name] = {
        "slots": sorted(set(slots)),
        "services": services,
        "email": email,
    }
    save_bookings(data)
    print(f"Barber '{name}' registered with {len(slots)} slot(s) and {len(services)} service(s).")


def list_barbers(data):
    """Display all registered barbers, their slots, and services."""
    print("\n== Registered Barbers ==")
    if not data["barbers"]:
        print("No barbers registered yet.")
        return

    for name, info in data["barbers"].items():
        slots_str = ", ".join(info.get("slots", [])) or "No slots"
        email_str = info.get("email") or "N/A"
        print(f"\n  {name} (email: {email_str})")
        print(f"    Slots: {slots_str}")
        services = info.get("services", {})
        if services:
            print("    Services:")
            for svc, price in services.items():
                print(f"      - {svc}: ${price:.2f}")
        else:
            print("    Services: None listed")


# ── Booking logic ──────────────────────────────────────────────────


def _is_slot_taken(data, barber, date, time_slot):
    """Check whether a specific slot is already booked."""
    for b in data["bookings"]:
        if b["barber"] == barber and b["date"] == date and b["time"] == time_slot:
            return True
    return False


def _select_barber(data):
    """Prompt user to select a barber. Returns name or None."""
    barber_names = list(data["barbers"].keys())
    print("Available barbers:")
    for i, name in enumerate(barber_names, 1):
        print(f"  {i}. {name}")
    choice = input("Select barber (number): ").strip()
    try:
        return barber_names[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None


def _select_date():
    """Prompt user for a date. Returns date string or None."""
    date_str = input("Date (YYYY-MM-DD): ").strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        print("Invalid date format.")
        return None


def _select_free_slot(data, barber, date_str):
    """Show free slots and let user pick one. Returns slot string or None."""
    all_slots = data["barbers"][barber].get("slots", [])
    free_slots = [s for s in all_slots if not _is_slot_taken(data, barber, date_str, s)]

    if not free_slots:
        print(f"No available slots for {barber} on {date_str}.")
        return None

    print(f"Available slots for {barber} on {date_str}:")
    for i, slot in enumerate(free_slots, 1):
        print(f"  {i}. {slot}")

    slot_choice = input("Select slot (number): ").strip()
    try:
        return free_slots[int(slot_choice) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None


def _select_service(data, barber):
    """Prompt user to pick a service. Returns (service_name, price) or (None, 0)."""
    services = data["barbers"][barber].get("services", {})
    if not services:
        return None, 0.0

    svc_list = list(services.items())
    print(f"Services offered by {barber}:")
    for i, (svc, price) in enumerate(svc_list, 1):
        print(f"  {i}. {svc} - ${price:.2f}")

    choice = input("Select service (number, or Enter to skip): ").strip()
    if not choice:
        return None, 0.0
    try:
        svc_name, svc_price = svc_list[int(choice) - 1]
        return svc_name, svc_price
    except (ValueError, IndexError):
        print("Invalid selection. No service selected.")
        return None, 0.0


def book_appointment(data):
    """Book an appointment with a barber."""
    print("\n== Book an Appointment ==")

    if not data["barbers"]:
        print("No barbers available. Register a barber first.")
        return

    barber = _select_barber(data)
    if not barber:
        return

    date_str = _select_date()
    if not date_str:
        return

    selected_slot = _select_free_slot(data, barber, date_str)
    if not selected_slot:
        return

    service, price = _select_service(data, barber)

    client_name = input("Your name: ").strip()
    if not client_name:
        print("Name cannot be empty.")
        return

    client_email = input("Your email (optional, press Enter to skip): ").strip()

    # Save booking
    booking = {
        "barber": barber,
        "client": client_name,
        "client_email": client_email,
        "date": date_str,
        "time": selected_slot,
        "service": service,
        "price": price,
        "booked_at": datetime.now().isoformat(),
    }
    data["bookings"].append(booking)
    save_bookings(data)

    svc_text = f" for {service} (${price:.2f})" if service else ""

    notify(
        "barber", barber,
        f"New appointment! {client_name} booked on {date_str} at {selected_slot}{svc_text}.",
        email=_barber_email(data, barber),
    )
    notify(
        "client", client_name,
        f"Confirmed! Your appointment with {barber} is on {date_str} at {selected_slot}{svc_text}.",
        email=client_email,
    )


def view_bookings(data):
    """Display all bookings split into upcoming and past."""
    print("\n== All Bookings ==")
    if not data["bookings"]:
        print("No bookings yet.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = [b for b in data["bookings"] if b["date"] >= today]
    past = [b for b in data["bookings"] if b["date"] < today]

    def _fmt(b):
        svc = b.get("service")
        svc_text = f" [{svc} ${b.get('price', 0):.2f}]" if svc else ""
        return f"  {b['date']} {b['time']} - {b['client']} with {b['barber']}{svc_text}"

    if upcoming:
        print("Upcoming:")
        for b in sorted(upcoming, key=lambda x: (x["date"], x["time"])):
            print(_fmt(b))

    if past:
        print("Past:")
        for b in sorted(past, key=lambda x: (x["date"], x["time"])):
            print(_fmt(b))


def _select_booking(data, prompt="Select booking (number): "):
    """Display bookings and let user pick one. Returns (index, booking) or (None, None)."""
    if not data["bookings"]:
        print("No bookings found.")
        return None, None

    for i, b in enumerate(data["bookings"], 1):
        svc = b.get("service")
        svc_text = f" [{svc} ${b.get('price', 0):.2f}]" if svc else ""
        print(f"  {i}. {b['date']} {b['time']} - {b['client']} with {b['barber']}{svc_text}")

    choice = input(prompt).strip()
    try:
        idx = int(choice) - 1
        return idx, data["bookings"][idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None, None


def cancel_booking(data):
    """Cancel an existing booking and notify both parties."""
    print("\n== Cancel a Booking ==")

    idx, booking = _select_booking(data)
    if booking is None:
        return

    confirm = input(
        f"Cancel {booking['client']}'s appointment on {booking['date']} at {booking['time']}? (y/n): "
    ).strip().lower()
    if confirm != "y":
        print("Cancellation aborted.")
        return

    removed = data["bookings"].pop(idx)
    save_bookings(data)

    notify(
        "barber", removed["barber"],
        f"Cancelled: {removed['client']}'s appointment on {removed['date']} at {removed['time']}.",
        email=_barber_email(data, removed["barber"]),
    )
    notify(
        "client", removed["client"],
        f"Your appointment with {removed['barber']} on {removed['date']} at {removed['time']} has been cancelled.",
        email=removed.get("client_email"),
    )


def reschedule_booking(data):
    """Reschedule an existing booking to a new date/time."""
    print("\n== Reschedule a Booking ==")

    idx, booking = _select_booking(data, prompt="Select booking to reschedule (number): ")
    if booking is None:
        return

    barber = booking["barber"]
    old_date = booking["date"]
    old_time = booking["time"]

    print(f"\nCurrent: {old_date} at {old_time} with {barber}")
    print("Pick a new date and slot:")

    new_date = _select_date()
    if not new_date:
        return

    new_slot = _select_free_slot(data, barber, new_date)
    if not new_slot:
        return

    # Update booking in place
    booking["date"] = new_date
    booking["time"] = new_slot
    booking["booked_at"] = datetime.now().isoformat()
    save_bookings(data)

    svc = booking.get("service")
    svc_text = f" for {svc}" if svc else ""

    notify(
        "barber", barber,
        f"Rescheduled: {booking['client']}'s appointment moved from {old_date} {old_time} to {new_date} {new_slot}{svc_text}.",
        email=_barber_email(data, barber),
    )
    notify(
        "client", booking["client"],
        f"Rescheduled! Your appointment with {barber} moved from {old_date} {old_time} to {new_date} {new_slot}{svc_text}.",
        email=booking.get("client_email"),
    )


def search_bookings(data):
    """Search bookings by barber or client name."""
    print("\n== Search Bookings ==")
    term = input("Search (barber or client name): ").strip().lower()
    if not term:
        print("Search term cannot be empty.")
        return

    results = [
        b for b in data["bookings"]
        if term in b["barber"].lower() or term in b["client"].lower()
    ]

    if not results:
        print(f"No bookings found matching '{term}'.")
        return

    print(f"Found {len(results)} booking(s):")
    for b in sorted(results, key=lambda x: (x["date"], x["time"])):
        svc = b.get("service")
        svc_text = f" [{svc} ${b.get('price', 0):.2f}]" if svc else ""
        print(f"  {b['date']} {b['time']} - {b['client']} with {b['barber']}{svc_text}")


# ── Main menu ──────────────────────────────────────────────────────


MENU = """
========================================
        Barber Booking Agent
========================================
  1. Register a barber
  2. List barbers
  3. Book an appointment
  4. View all bookings
  5. Cancel a booking
  6. Reschedule a booking
  7. Search bookings
  8. Exit
========================================"""


def main():
    data = load_bookings()

    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()

        if choice == "1":
            register_barber(data)
        elif choice == "2":
            list_barbers(data)
        elif choice == "3":
            book_appointment(data)
        elif choice == "4":
            view_bookings(data)
        elif choice == "5":
            cancel_booking(data)
        elif choice == "6":
            reschedule_booking(data)
        elif choice == "7":
            search_bookings(data)
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
