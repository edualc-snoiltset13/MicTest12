"""Pure booking, search, and partition logic."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from barber_booking.models import Booking, NewBooking, Store, with_bookings

__all__ = [
    "is_slot_taken",
    "free_slots",
    "add_booking",
    "remove_booking",
    "reschedule",
    "search",
    "partition_upcoming_past",
    "sort_by_date_time",
    "parse_date",
    "parse_time",
    "parse_price",
]


def is_slot_taken(store: Store, barber: str, date: str, time: str) -> bool:
    return any(
        b.barber == barber and b.date == date and b.time == time
        for b in store.bookings
    )


def free_slots(store: Store, barber: str, date: str) -> list[str]:
    b = store.barbers.get(barber)
    if b is None:
        return []
    return [s for s in b.slots if not is_slot_taken(store, barber, date, s)]


def add_booking(store: Store, nb: NewBooking, booked_at: str) -> Store:
    booking = Booking(
        barber=nb.barber,
        client=nb.client,
        client_email=nb.client_email,
        date=nb.date,
        time=nb.time,
        service=nb.service,
        price=nb.price,
        booked_at=booked_at,
    )
    return with_bookings(store, store.bookings + (booking,))


def remove_booking(store: Store, index: int) -> tuple[Store, Booking]:
    if index < 0 or index >= len(store.bookings):
        raise IndexError(index)
    removed = store.bookings[index]
    new = store.bookings[:index] + store.bookings[index + 1 :]
    return with_bookings(store, new), removed


def reschedule(
    store: Store,
    index: int,
    new_date: str,
    new_time: str,
    booked_at: str,
) -> tuple[Store, Booking, Booking]:
    if index < 0 or index >= len(store.bookings):
        raise IndexError(index)
    old = store.bookings[index]
    new_booking = Booking(
        barber=old.barber,
        client=old.client,
        client_email=old.client_email,
        date=new_date,
        time=new_time,
        service=old.service,
        price=old.price,
        booked_at=booked_at,
    )
    new_bookings = (
        store.bookings[:index] + (new_booking,) + store.bookings[index + 1 :]
    )
    return with_bookings(store, new_bookings), old, new_booking


def search(store: Store, term: str) -> list[Booking]:
    t = term.lower()
    return [
        b for b in store.bookings if t in b.barber.lower() or t in b.client.lower()
    ]


def partition_upcoming_past(
    store: Store, today: str
) -> tuple[list[Booking], list[Booking]]:
    upcoming = [b for b in store.bookings if b.date >= today]
    past = [b for b in store.bookings if b.date < today]
    return upcoming, past


def sort_by_date_time(bs: Sequence[Booking]) -> list[Booking]:
    return sorted(bs, key=lambda x: (x.date, x.time))


def parse_date(s: str) -> str | None:
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None
    return s


def parse_time(s: str) -> str | None:
    try:
        datetime.strptime(s, "%H:%M")
    except ValueError:
        return None
    return s


def parse_price(s: str) -> float | None:
    try:
        return round(float(s), 2)
    except ValueError:
        return None
