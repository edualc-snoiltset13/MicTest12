"""
Barber Booking Agent
A simple Python agent that manages barber appointment bookings,
maintains a calendar, and notifies both the barber and the client.
"""

import json
import os
from datetime import datetime, timedelta

DATA_FILE = "bookings.json"


def load_bookings():
    """Load bookings from the JSON data file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"barbers": {}, "bookings": [], "next_token": 1}


def save_bookings(data):
    """Persist bookings to the JSON data file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def notify(recipient_type, name, message):
    """Send a notification (printed to console)."""
    tag = "BARBER" if recipient_type == "barber" else "CLIENT"
    print(f"\n--- Notification [{tag}] ---")
    print(f"To: {name}")
    print(f"Message: {message}")
    print("----------------------------\n")


# ── Barber management ──────────────────────────────────────────────


def register_barber(data):
    """Register a new barber with available time slots."""
    print("\n== Register a Barber ==")
    name = input("Barber name: ").strip()
    if not name:
        print("Name cannot be empty.")
        return

    if name in data["barbers"]:
        print(f"Barber '{name}' is already registered.")
        return

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

    data["barbers"][name] = {"slots": sorted(set(slots))}
    save_bookings(data)
    print(f"Barber '{name}' registered with {len(slots)} slot(s).")


def list_barbers(data):
    """Display all registered barbers and their slots."""
    print("\n== Registered Barbers ==")
    if not data["barbers"]:
        print("No barbers registered yet.")
        return

    for name, info in data["barbers"].items():
        slots_str = ", ".join(info["slots"]) if info["slots"] else "No slots"
        print(f"  {name}: {slots_str}")


# ── Booking logic ──────────────────────────────────────────────────


def _is_slot_taken(data, barber, date, time_slot):
    """Check whether a specific slot is already booked."""
    for b in data["bookings"]:
        if b["barber"] == barber and b["date"] == date and b["time"] == time_slot:
            return True
    return False


def book_appointment(data):
    """Book an appointment with a barber."""
    print("\n== Book an Appointment ==")

    if not data["barbers"]:
        print("No barbers available. Register a barber first.")
        return

    # Choose barber
    barber_names = list(data["barbers"].keys())
    print("Available barbers:")
    for i, name in enumerate(barber_names, 1):
        print(f"  {i}. {name}")

    choice = input("Select barber (number): ").strip()
    try:
        barber = barber_names[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    # Choose date
    date_str = input("Date (YYYY-MM-DD): ").strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format.")
        return

    # Show available (not-yet-booked) slots
    all_slots = data["barbers"][barber]["slots"]
    free_slots = [s for s in all_slots if not _is_slot_taken(data, barber, date_str, s)]

    if not free_slots:
        print(f"No available slots for {barber} on {date_str}.")
        return

    print(f"Available slots for {barber} on {date_str}:")
    for i, slot in enumerate(free_slots, 1):
        print(f"  {i}. {slot}")

    slot_choice = input("Select slot (number): ").strip()
    try:
        selected_slot = free_slots[int(slot_choice) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    client_name = input("Your name: ").strip()
    if not client_name:
        print("Name cannot be empty.")
        return

    # Assign token number
    token = data.get("next_token", 1)
    data["next_token"] = token + 1

    # Save booking
    booking = {
        "token": token,
        "barber": barber,
        "client": client_name,
        "date": date_str,
        "time": selected_slot,
        "booked_at": datetime.now().isoformat(),
    }
    data["bookings"].append(booking)
    save_bookings(data)

    print(f"\nYour token number is: #{token}")

    # Notify both parties
    notify(
        "barber",
        barber,
        f"New appointment! Token #{token} - {client_name} booked on {date_str} at {selected_slot}.",
    )
    notify(
        "client",
        client_name,
        f"Confirmed! Token #{token} - Your appointment with {barber} is on {date_str} at {selected_slot}.",
    )


def view_bookings(data):
    """Display all upcoming bookings."""
    print("\n== All Bookings ==")
    if not data["bookings"]:
        print("No bookings yet.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = [b for b in data["bookings"] if b["date"] >= today]
    past = [b for b in data["bookings"] if b["date"] < today]

    if upcoming:
        print("Upcoming:")
        for b in sorted(upcoming, key=lambda x: (x["date"], x["time"])):
            token = b.get("token", "N/A")
            print(f"  [Token #{token}] {b['date']} {b['time']} - {b['client']} with {b['barber']}")

    if past:
        print("Past:")
        for b in sorted(past, key=lambda x: (x["date"], x["time"])):
            token = b.get("token", "N/A")
            print(f"  [Token #{token}] {b['date']} {b['time']} - {b['client']} with {b['barber']}")


def cancel_booking(data):
    """Cancel an existing booking and notify both parties."""
    print("\n== Cancel a Booking ==")
    if not data["bookings"]:
        print("No bookings to cancel.")
        return

    for i, b in enumerate(data["bookings"], 1):
        token = b.get("token", "N/A")
        print(f"  {i}. [Token #{token}] {b['date']} {b['time']} - {b['client']} with {b['barber']}")

    choice = input("Select booking to cancel (number): ").strip()
    try:
        idx = int(choice) - 1
        booking = data["bookings"][idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    token = booking.get("token", "N/A")
    confirm = input(f"Cancel Token #{token} - {booking['client']}'s appointment on {booking['date']} at {booking['time']}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancellation aborted.")
        return

    removed = data["bookings"].pop(idx)
    save_bookings(data)

    removed_token = removed.get("token", "N/A")
    notify(
        "barber",
        removed["barber"],
        f"Cancelled: Token #{removed_token} - {removed['client']}'s appointment on {removed['date']} at {removed['time']}.",
    )
    notify(
        "client",
        removed["client"],
        f"Token #{removed_token} - Your appointment with {removed['barber']} on {removed['date']} at {removed['time']} has been cancelled.",
    )


# ── Token lookup ──────────────────────────────────────────────────


def lookup_by_token(data):
    """Look up a booking by its token number."""
    print("\n== Look Up Booking by Token ==")
    if not data["bookings"]:
        print("No bookings yet.")
        return

    token_input = input("Enter token number: ").strip().lstrip("#")
    try:
        token_num = int(token_input)
    except ValueError:
        print("Invalid token number.")
        return

    found = [b for b in data["bookings"] if b.get("token") == token_num]
    if not found:
        print(f"No booking found with Token #{token_num}.")
        return

    for b in found:
        print(f"\n  Token:   #{b['token']}")
        print(f"  Client:  {b['client']}")
        print(f"  Barber:  {b['barber']}")
        print(f"  Date:    {b['date']}")
        print(f"  Time:    {b['time']}")
        print(f"  Booked:  {b['booked_at']}")


# ── Main menu ──────────────────────────────────────────────────────


MENU = """
=============================
  Barber Booking Agent
=============================
  1. Register a barber
  2. List barbers
  3. Book an appointment
  4. View bookings
  5. Cancel a booking
  6. Look up booking by token
  7. Exit
============================="""


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
            lookup_by_token(data)
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
