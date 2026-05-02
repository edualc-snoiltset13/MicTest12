"""Exhaustive tests for the pure booking logic."""

from __future__ import annotations

import pytest

from barber_booking.booking import (
    add_booking,
    free_slots,
    is_slot_taken,
    parse_date,
    parse_price,
    parse_time,
    partition_upcoming_past,
    remove_booking,
    reschedule,
    search,
    sort_by_date_time,
)
from barber_booking.models import Booking, NewBooking, Store


# ── is_slot_taken ─────────────────────────────────────────────────────


def test_is_slot_taken_exact_match(sample_store: Store) -> None:
    assert is_slot_taken(sample_store, "Alice", "2026-04-01", "09:00") is True


def test_is_slot_taken_different_barber(sample_store: Store) -> None:
    assert is_slot_taken(sample_store, "Bob", "2026-04-01", "09:00") is False


def test_is_slot_taken_different_date(sample_store: Store) -> None:
    assert is_slot_taken(sample_store, "Alice", "2026-04-02", "09:00") is False


def test_is_slot_taken_different_time(sample_store: Store) -> None:
    assert is_slot_taken(sample_store, "Alice", "2026-04-01", "10:00") is False


def test_is_slot_taken_empty_store_is_false() -> None:
    assert is_slot_taken(Store(), "Alice", "2026-04-01", "09:00") is False


# ── free_slots ────────────────────────────────────────────────────────


def test_free_slots_excludes_taken(sample_store: Store) -> None:
    assert free_slots(sample_store, "Alice", "2026-04-01") == ["10:00", "11:00"]


def test_free_slots_all_available_when_no_bookings(sample_store: Store) -> None:
    assert free_slots(sample_store, "Alice", "2099-01-01") == [
        "09:00",
        "10:00",
        "11:00",
    ]


def test_free_slots_unknown_barber_returns_empty(sample_store: Store) -> None:
    assert free_slots(sample_store, "Zoe", "2026-04-01") == []


# ── add / remove / reschedule ────────────────────────────────────────


def test_add_booking_appends_with_booked_at(sample_store: Store) -> None:
    nb = NewBooking(
        barber="Alice",
        client="Frank",
        client_email="frank@example.com",
        date="2026-06-01",
        time="11:00",
        service=None,
        price=0.0,
    )
    new_store = add_booking(sample_store, nb, "2026-05-02T10:00:00")
    assert len(new_store.bookings) == len(sample_store.bookings) + 1
    added = new_store.bookings[-1]
    assert added.booked_at == "2026-05-02T10:00:00"
    assert added.client == "Frank"


def test_add_booking_does_not_mutate_input(sample_store: Store) -> None:
    nb = NewBooking("Alice", "Frank", "", "2026-06-01", "11:00", None, 0.0)
    add_booking(sample_store, nb, "ts")
    assert len(sample_store.bookings) == 3


def test_remove_booking_returns_removed(sample_store: Store) -> None:
    new_store, removed = remove_booking(sample_store, 0)
    assert removed.client == "Carol"
    assert len(new_store.bookings) == 2


def test_remove_booking_invalid_index(sample_store: Store) -> None:
    with pytest.raises(IndexError):
        remove_booking(sample_store, 99)
    with pytest.raises(IndexError):
        remove_booking(sample_store, -1)


def test_reschedule_updates_date_time_and_booked_at(sample_store: Store) -> None:
    new_store, old, new = reschedule(
        sample_store, 0, "2026-04-15", "11:00", "2026-04-10T08:00:00"
    )
    assert old.date == "2026-04-01" and old.time == "09:00"
    assert new.date == "2026-04-15" and new.time == "11:00"
    assert new.booked_at == "2026-04-10T08:00:00"
    assert new.client == old.client
    assert new_store.bookings[0] == new


def test_reschedule_invalid_index(sample_store: Store) -> None:
    with pytest.raises(IndexError):
        reschedule(sample_store, 99, "2026-04-15", "11:00", "ts")


# ── search ────────────────────────────────────────────────────────────


def test_search_case_insensitive_barber(sample_store: Store) -> None:
    assert len(search(sample_store, "alice")) == 2
    assert len(search(sample_store, "ALICE")) == 2


def test_search_matches_client(sample_store: Store) -> None:
    results = search(sample_store, "carol")
    assert len(results) == 1 and results[0].client == "Carol"


def test_search_partial_match(sample_store: Store) -> None:
    assert len(search(sample_store, "li")) == 2  # matches "Alice"


def test_search_no_match(sample_store: Store) -> None:
    assert search(sample_store, "zoe") == []


# ── partition / sort ─────────────────────────────────────────────────


def test_partition_treats_today_as_upcoming(sample_store: Store) -> None:
    upcoming, past = partition_upcoming_past(sample_store, "2026-04-01")
    assert any(b.date == "2026-04-01" for b in upcoming)
    assert all(b.date < "2026-04-01" for b in past)


def test_partition_strict_past(sample_store: Store) -> None:
    upcoming, past = partition_upcoming_past(sample_store, "2026-04-02")
    assert any(b.date == "2026-04-01" for b in past)
    assert all(b.date >= "2026-04-02" for b in upcoming)


def test_sort_by_date_time(sample_store: Store) -> None:
    sorted_b = sort_by_date_time(sample_store.bookings)
    assert [b.date for b in sorted_b] == ["2026-04-01", "2026-05-10", "2026-05-10"]
    same_date = [b for b in sorted_b if b.date == "2026-05-10"]
    assert [b.time for b in same_date] == ["10:00", "13:00"]


# ── parsers ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value,expected",
    [
        ("2026-05-02", "2026-05-02"),
        ("not-a-date", None),
        ("", None),
        ("2026/05/02", None),
    ],
)
def test_parse_date(value: str, expected: str | None) -> None:
    assert parse_date(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("09:00", "09:00"),
        ("23:59", "23:59"),
        ("9:00", "9:00"),  # strptime accepts single-digit hour
        ("noon", None),
        ("", None),
    ],
)
def test_parse_time(value: str, expected: str | None) -> None:
    assert parse_time(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        ("25", 25.0),
        ("25.50", 25.5),
        ("25.999", 26.0),
        ("free", None),
        ("", None),
    ],
)
def test_parse_price(value: str, expected: float | None) -> None:
    assert parse_price(value) == expected


def test_added_booking_serializes_with_no_existing_collision() -> None:
    """Booking the same slot twice should be possible at the data layer.

    Slot-collision protection happens at the prompt layer (`free_slots`); the
    data functions themselves don't enforce it. This documents that boundary.
    """
    store = Store()
    nb = NewBooking("Alice", "Carol", "", "2026-04-01", "09:00", None, 0.0)
    store = add_booking(store, nb, "ts1")
    store = add_booking(store, nb, "ts2")
    assert len(store.bookings) == 2


def test_booking_immutability_of_tuple(sample_store: Store) -> None:
    """Bookings tuple is immutable in Python — sanity check."""
    with pytest.raises((TypeError, AttributeError)):
        sample_store.bookings.append(  # type: ignore[attr-defined]
            Booking("X", "Y", "Z", "2026-01-01", "09:00", "")
        )
