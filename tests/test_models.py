"""Round-trip and shape tests for models.py."""

from __future__ import annotations

from barber_booking.models import (
    Barber,
    Booking,
    Store,
    barber_from_dict,
    barber_to_dict,
    booking_from_dict,
    booking_to_dict,
    empty_store,
    store_from_dict,
    store_to_dict,
)


def test_empty_store_defaults() -> None:
    s = empty_store()
    assert s.barbers == {}
    assert s.bookings == ()


def test_barber_round_trip() -> None:
    raw = {
        "slots": ["09:00", "10:00"],
        "services": {"Haircut": 25.0},
        "email": "alice@example.com",
    }
    b = barber_from_dict("Alice", raw)
    assert b == Barber(
        name="Alice",
        slots=("09:00", "10:00"),
        services={"Haircut": 25.0},
        email="alice@example.com",
    )
    assert barber_to_dict(b) == raw


def test_barber_missing_optional_keys_get_defaults() -> None:
    b = barber_from_dict("Bob", {"slots": [], "services": {}, "email": ""})
    assert b.email == ""
    assert b.slots == ()
    assert b.services == {}


def test_booking_round_trip_with_service() -> None:
    raw = {
        "barber": "Alice",
        "client": "Carol",
        "client_email": "carol@example.com",
        "date": "2026-04-01",
        "time": "09:00",
        "service": "Haircut",
        "price": 25.0,
        "booked_at": "2026-03-30T12:00:00",
    }
    b = booking_from_dict(raw)  # type: ignore[arg-type]
    assert booking_to_dict(b) == raw


def test_booking_round_trip_without_service() -> None:
    raw = {
        "barber": "Bob",
        "client": "Dan",
        "client_email": "",
        "date": "2026-05-10",
        "time": "13:00",
        "service": None,
        "price": 0.0,
        "booked_at": "2026-04-25T09:00:00",
    }
    b = booking_from_dict(raw)  # type: ignore[arg-type]
    assert b.service is None
    assert b.price == 0.0
    assert booking_to_dict(b) == raw


def test_booking_defaults_match_legacy_omissions() -> None:
    raw = {
        "barber": "Alice",
        "client": "Carol",
        "date": "2026-04-01",
        "time": "09:00",
    }
    b = booking_from_dict(raw)  # type: ignore[arg-type]
    assert b.client_email == ""
    assert b.service is None
    assert b.price == 0.0
    assert b.booked_at == ""


def test_store_round_trip(sample_store: Store) -> None:
    d = store_to_dict(sample_store)
    assert store_from_dict(d) == sample_store
