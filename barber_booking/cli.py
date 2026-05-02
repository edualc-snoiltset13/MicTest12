"""Interactive CLI: prompts (input), renderers (print), action handlers, run loop.

All input/output goes through the injectable `Reader` and `Writer` callables on
`Deps`, which keeps the action handlers testable without monkeypatching globals.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Mapping

from barber_booking import booking as bk
from barber_booking import store as st
from barber_booking.models import (
    Barber,
    Booking,
    NewBarber,
    NewBooking,
    Store,
)
from barber_booking.notifications import notify
from barber_booking.persistence import DEFAULT_DATA_FILE, load_store, save_store

Reader = Callable[[str], str]
Writer = Callable[[str], None]


@dataclass
class Deps:
    reader: Reader = input
    writer: Writer = field(default=lambda s: print(s))
    now: Callable[[], datetime] = datetime.now
    env: Mapping[str, str] = field(default_factory=lambda: dict(os.environ))
    data_file: str = DEFAULT_DATA_FILE


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


# ── Prompts (input only) ───────────────────────────────────────────


def prompt_barber_registration(
    store: Store, reader: Reader, writer: Writer
) -> NewBarber | None:
    writer("\n== Register a Barber ==")
    name = reader("Barber name: ").strip()
    if not name:
        writer("Name cannot be empty.")
        return None
    if st.has_barber(store, name):
        writer(f"Barber '{name}' is already registered.")
        return None

    email = reader("Barber email (optional, press Enter to skip): ").strip()

    writer("Enter available time slots (24-hr format, e.g. 09:00).")
    writer("Type 'done' when finished.")
    slots: list[str] = []
    while True:
        slot = reader("  Slot: ").strip()
        if slot.lower() == "done":
            break
        if bk.parse_time(slot) is None:
            writer("  Invalid format. Use HH:MM (e.g. 09:00).")
            continue
        slots.append(slot)

    writer("Enter services with prices (e.g. Haircut, then 25.00).")
    writer("Type 'done' when finished.")
    services: dict[str, float] = {}
    while True:
        entry = reader("  Service name: ").strip()
        if entry.lower() == "done":
            break
        if not entry:
            continue
        price_str = reader(f"  Price for '{entry}': ").strip()
        price = bk.parse_price(price_str)
        if price is None:
            writer("  Invalid price. Skipping this service.")
            continue
        services[entry] = price

    return NewBarber(
        name=name,
        email=email,
        slots=tuple(sorted(set(slots))),
        services=services,
    )


def prompt_select_barber(
    store: Store, reader: Reader, writer: Writer
) -> str | None:
    names = st.list_barber_names(store)
    writer("Available barbers:")
    for i, name in enumerate(names, 1):
        writer(f"  {i}. {name}")
    choice = reader("Select barber (number): ").strip()
    try:
        return names[int(choice) - 1]
    except (ValueError, IndexError):
        writer("Invalid selection.")
        return None


def prompt_date(reader: Reader, writer: Writer) -> str | None:
    raw = reader("Date (YYYY-MM-DD): ").strip()
    parsed = bk.parse_date(raw)
    if parsed is None:
        writer("Invalid date format.")
    return parsed


def prompt_select_free_slot(
    store: Store, barber: str, date: str, reader: Reader, writer: Writer
) -> str | None:
    free = bk.free_slots(store, barber, date)
    if not free:
        writer(f"No available slots for {barber} on {date}.")
        return None
    writer(f"Available slots for {barber} on {date}:")
    for i, slot in enumerate(free, 1):
        writer(f"  {i}. {slot}")
    choice = reader("Select slot (number): ").strip()
    try:
        return free[int(choice) - 1]
    except (ValueError, IndexError):
        writer("Invalid selection.")
        return None


def prompt_select_service(
    store: Store, barber: str, reader: Reader, writer: Writer
) -> tuple[str | None, float]:
    b = st.get_barber(store, barber)
    services = list(b.services.items()) if b else []
    if not services:
        return None, 0.0
    writer(f"Services offered by {barber}:")
    for i, (svc, price) in enumerate(services, 1):
        writer(f"  {i}. {svc} - ${price:.2f}")
    choice = reader("Select service (number, or Enter to skip): ").strip()
    if not choice:
        return None, 0.0
    try:
        svc, price = services[int(choice) - 1]
        return svc, price
    except (ValueError, IndexError):
        writer("Invalid selection. No service selected.")
        return None, 0.0


def prompt_select_booking(
    store: Store,
    reader: Reader,
    writer: Writer,
    prompt: str = "Select booking (number): ",
) -> int | None:
    if not store.bookings:
        writer("No bookings found.")
        return None
    for i, b in enumerate(store.bookings, 1):
        writer(f"  {i}. {render_booking_line(b)}")
    choice = reader(prompt).strip()
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(store.bookings):
            raise IndexError
        return idx
    except (ValueError, IndexError):
        writer("Invalid selection.")
        return None


def prompt_confirm(question: str, reader: Reader) -> bool:
    return reader(question).strip().lower() == "y"


# ── Renderers (output only) ────────────────────────────────────────


def render_booking_line(b: Booking) -> str:
    svc_text = f" [{b.service} ${b.price:.2f}]" if b.service else ""
    return f"{b.date} {b.time} - {b.client} with {b.barber}{svc_text}"


def render_menu(writer: Writer) -> None:
    writer(MENU)


def render_barbers(store: Store, writer: Writer) -> None:
    writer("\n== Registered Barbers ==")
    if not store.barbers:
        writer("No barbers registered yet.")
        return
    for name, info in store.barbers.items():
        slots_str = ", ".join(info.slots) or "No slots"
        email_str = info.email or "N/A"
        writer(f"\n  {name} (email: {email_str})")
        writer(f"    Slots: {slots_str}")
        if info.services:
            writer("    Services:")
            for svc, price in info.services.items():
                writer(f"      - {svc}: ${price:.2f}")
        else:
            writer("    Services: None listed")


def render_bookings(store: Store, today: str, writer: Writer) -> None:
    writer("\n== All Bookings ==")
    if not store.bookings:
        writer("No bookings yet.")
        return
    upcoming, past = bk.partition_upcoming_past(store, today)
    if upcoming:
        writer("Upcoming:")
        for b in bk.sort_by_date_time(upcoming):
            writer(f"  {render_booking_line(b)}")
    if past:
        writer("Past:")
        for b in bk.sort_by_date_time(past):
            writer(f"  {render_booking_line(b)}")


def render_search_results(results: list[Booking], term: str, writer: Writer) -> None:
    if not results:
        writer(f"No bookings found matching '{term}'.")
        return
    writer(f"Found {len(results)} booking(s):")
    for b in bk.sort_by_date_time(results):
        writer(f"  {render_booking_line(b)}")


# ── Action handlers ────────────────────────────────────────────────


def _persist(store: Store, deps: Deps) -> None:
    save_store(store, deps.data_file)


def action_register_barber(store: Store, deps: Deps) -> Store:
    nb = prompt_barber_registration(store, deps.reader, deps.writer)
    if nb is None:
        return store
    barber = Barber(
        name=nb.name, slots=nb.slots, services=dict(nb.services), email=nb.email
    )
    new_store = st.add_barber(store, barber)
    _persist(new_store, deps)
    deps.writer(
        f"Barber '{nb.name}' registered with {len(nb.slots)} slot(s) "
        f"and {len(nb.services)} service(s)."
    )
    return new_store


def action_list_barbers(store: Store, deps: Deps) -> Store:
    render_barbers(store, deps.writer)
    return store


def action_book(store: Store, deps: Deps) -> Store:
    deps.writer("\n== Book an Appointment ==")
    if not store.barbers:
        deps.writer("No barbers available. Register a barber first.")
        return store

    barber = prompt_select_barber(store, deps.reader, deps.writer)
    if barber is None:
        return store
    date = prompt_date(deps.reader, deps.writer)
    if date is None:
        return store
    slot = prompt_select_free_slot(store, barber, date, deps.reader, deps.writer)
    if slot is None:
        return store

    service, price = prompt_select_service(store, barber, deps.reader, deps.writer)

    client = deps.reader("Your name: ").strip()
    if not client:
        deps.writer("Name cannot be empty.")
        return store
    client_email = deps.reader(
        "Your email (optional, press Enter to skip): "
    ).strip()

    nb = NewBooking(
        barber=barber,
        client=client,
        client_email=client_email,
        date=date,
        time=slot,
        service=service,
        price=price,
    )
    new_store = bk.add_booking(store, nb, deps.now().isoformat())
    _persist(new_store, deps)

    svc_text = f" for {service} (${price:.2f})" if service else ""
    notify(
        "barber",
        barber,
        f"New appointment! {client} booked on {date} at {slot}{svc_text}.",
        email=st.barber_email(new_store, barber),
        printer=deps.writer,
        env=deps.env,
    )
    notify(
        "client",
        client,
        f"Confirmed! Your appointment with {barber} is on {date} at {slot}{svc_text}.",
        email=client_email,
        printer=deps.writer,
        env=deps.env,
    )
    return new_store


def action_view(store: Store, deps: Deps) -> Store:
    today = deps.now().strftime("%Y-%m-%d")
    render_bookings(store, today, deps.writer)
    return store


def action_cancel(store: Store, deps: Deps) -> Store:
    deps.writer("\n== Cancel a Booking ==")
    idx = prompt_select_booking(store, deps.reader, deps.writer)
    if idx is None:
        return store
    booking = store.bookings[idx]
    confirmed = prompt_confirm(
        f"Cancel {booking.client}'s appointment on {booking.date} at "
        f"{booking.time}? (y/n): ",
        deps.reader,
    )
    if not confirmed:
        deps.writer("Cancellation aborted.")
        return store
    new_store, removed = bk.remove_booking(store, idx)
    _persist(new_store, deps)
    notify(
        "barber",
        removed.barber,
        f"Cancelled: {removed.client}'s appointment on {removed.date} at "
        f"{removed.time}.",
        email=st.barber_email(new_store, removed.barber),
        printer=deps.writer,
        env=deps.env,
    )
    notify(
        "client",
        removed.client,
        f"Your appointment with {removed.barber} on {removed.date} at "
        f"{removed.time} has been cancelled.",
        email=removed.client_email,
        printer=deps.writer,
        env=deps.env,
    )
    return new_store


def action_reschedule(store: Store, deps: Deps) -> Store:
    deps.writer("\n== Reschedule a Booking ==")
    idx = prompt_select_booking(
        store,
        deps.reader,
        deps.writer,
        prompt="Select booking to reschedule (number): ",
    )
    if idx is None:
        return store
    booking = store.bookings[idx]
    deps.writer(
        f"\nCurrent: {booking.date} at {booking.time} with {booking.barber}"
    )
    deps.writer("Pick a new date and slot:")
    new_date = prompt_date(deps.reader, deps.writer)
    if new_date is None:
        return store
    new_slot = prompt_select_free_slot(
        store, booking.barber, new_date, deps.reader, deps.writer
    )
    if new_slot is None:
        return store
    new_store, old, new_b = bk.reschedule(
        store, idx, new_date, new_slot, deps.now().isoformat()
    )
    _persist(new_store, deps)

    svc_text = f" for {new_b.service}" if new_b.service else ""
    notify(
        "barber",
        new_b.barber,
        f"Rescheduled: {new_b.client}'s appointment moved from "
        f"{old.date} {old.time} to {new_b.date} {new_b.time}{svc_text}.",
        email=st.barber_email(new_store, new_b.barber),
        printer=deps.writer,
        env=deps.env,
    )
    notify(
        "client",
        new_b.client,
        f"Rescheduled! Your appointment with {new_b.barber} moved from "
        f"{old.date} {old.time} to {new_b.date} {new_b.time}{svc_text}.",
        email=new_b.client_email,
        printer=deps.writer,
        env=deps.env,
    )
    return new_store


def action_search(store: Store, deps: Deps) -> Store:
    deps.writer("\n== Search Bookings ==")
    term = deps.reader("Search (barber or client name): ").strip().lower()
    if not term:
        deps.writer("Search term cannot be empty.")
        return store
    results = bk.search(store, term)
    render_search_results(results, term, deps.writer)
    return store


# ── Loop ───────────────────────────────────────────────────────────


def run(deps: Deps | None = None) -> None:
    d = deps or Deps()
    store = load_store(d.data_file)

    actions: dict[str, Callable[[Store, Deps], Store]] = {
        "1": action_register_barber,
        "2": action_list_barbers,
        "3": action_book,
        "4": action_view,
        "5": action_cancel,
        "6": action_reschedule,
        "7": action_search,
    }

    while True:
        render_menu(d.writer)
        choice = d.reader("Choose an option: ").strip()
        if choice == "8":
            d.writer("Goodbye!")
            return
        action = actions.get(choice)
        if action is None:
            d.writer("Invalid option. Please try again.")
            continue
        store = action(store, d)
