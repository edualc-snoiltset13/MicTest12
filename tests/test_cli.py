"""End-to-end CLI flow tests using injected reader/writer."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable
from unittest import mock

from barber_booking.cli import (
    Deps,
    action_book,
    action_cancel,
    action_list_barbers,
    action_register_barber,
    action_reschedule,
    action_search,
    action_view,
    render_booking_line,
    run,
)
from barber_booking.models import Booking, Store
from barber_booking.persistence import load_store


# ── helpers ──────────────────────────────────────────────────────────


def _make_deps(
    inputs: list[str], outputs: list[str], data_file: Path
) -> Deps:
    def reader(_prompt: str) -> str:
        if not inputs:
            raise AssertionError("reader called with no inputs left")
        return inputs.pop(0)

    return Deps(
        reader=reader,
        writer=outputs.append,
        now=lambda: datetime(2026, 5, 2, 10, 0, 0),
        env={},
        data_file=str(data_file),
    )


# ── render_booking_line ──────────────────────────────────────────────


def test_render_booking_line_with_service() -> None:
    b = Booking("Alice", "Carol", "2026-04-01", "09:00", "ts", "", "Haircut", 25.0)
    assert render_booking_line(b) == "2026-04-01 09:00 - Carol with Alice [Haircut $25.00]"


def test_render_booking_line_without_service() -> None:
    b = Booking("Alice", "Carol", "2026-04-01", "09:00", "ts")
    assert render_booking_line(b) == "2026-04-01 09:00 - Carol with Alice"


# ── register ─────────────────────────────────────────────────────────


def test_register_barber_happy_path(tmp_data_file: Path) -> None:
    inputs = [
        "Alice",
        "alice@example.com",
        "09:00",
        "10:00",
        "done",
        "Haircut",
        "25.00",
        "done",
    ]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)

    new_store = action_register_barber(Store(), deps)
    assert "Alice" in new_store.barbers
    assert new_store.barbers["Alice"].email == "alice@example.com"
    assert new_store.barbers["Alice"].slots == ("09:00", "10:00")
    assert new_store.barbers["Alice"].services == {"Haircut": 25.0}

    persisted = load_store(str(tmp_data_file))
    assert "Alice" in persisted.barbers


def test_register_barber_empty_name_aborts(tmp_data_file: Path) -> None:
    inputs = [""]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)

    out = action_register_barber(Store(), deps)
    assert out == Store()
    assert any("Name cannot be empty" in line for line in outputs)


def test_register_barber_duplicate_rejected(
    seeded_data_file: Path, sample_store: Store
) -> None:
    inputs = ["Alice"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, seeded_data_file)

    out = action_register_barber(sample_store, deps)
    assert out == sample_store
    assert any("already registered" in line for line in outputs)


def test_register_barber_invalid_slot_skipped(tmp_data_file: Path) -> None:
    inputs = [
        "Carol",
        "",
        "noon",
        "09:00",
        "done",
        "done",
    ]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    new_store = action_register_barber(Store(), deps)
    assert new_store.barbers["Carol"].slots == ("09:00",)


def test_register_barber_invalid_price_skipped(tmp_data_file: Path) -> None:
    inputs = [
        "Carol",
        "",
        "done",
        "Haircut",
        "free",
        "done",
    ]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    new_store = action_register_barber(Store(), deps)
    assert new_store.barbers["Carol"].services == {}


# ── list_barbers / view ──────────────────────────────────────────────


def test_list_barbers_empty(tmp_data_file: Path) -> None:
    outputs: list[str] = []
    deps = _make_deps([], outputs, tmp_data_file)
    action_list_barbers(Store(), deps)
    assert any("No barbers registered" in line for line in outputs)


def test_list_barbers_renders_services(
    sample_store: Store, tmp_data_file: Path
) -> None:
    outputs: list[str] = []
    deps = _make_deps([], outputs, tmp_data_file)
    action_list_barbers(sample_store, deps)
    blob = "\n".join(outputs)
    assert "Alice" in blob and "Haircut" in blob
    assert "Bob" in blob and "None listed" in blob


def test_view_bookings_empty(tmp_data_file: Path) -> None:
    outputs: list[str] = []
    deps = _make_deps([], outputs, tmp_data_file)
    action_view(Store(), deps)
    assert any("No bookings yet" in line for line in outputs)


def test_view_bookings_partitions(
    sample_store: Store, tmp_data_file: Path
) -> None:
    outputs: list[str] = []
    deps = _make_deps([], outputs, tmp_data_file)
    action_view(sample_store, deps)
    blob = "\n".join(outputs)
    assert "Past:" in blob
    assert "Upcoming:" in blob


# ── book ─────────────────────────────────────────────────────────────


def test_book_happy_path(seeded_data_file: Path, sample_store: Store) -> None:
    inputs = [
        "1",          # select Alice
        "2026-06-01", # date
        "1",          # first free slot
        "1",          # first service (Haircut)
        "Frank",
        "frank@example.com",
    ]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, seeded_data_file)

    new_store = action_book(sample_store, deps)
    assert len(new_store.bookings) == len(sample_store.bookings) + 1
    persisted = load_store(str(seeded_data_file))
    assert any(b.client == "Frank" for b in persisted.bookings)


def test_book_no_barbers(tmp_data_file: Path) -> None:
    outputs: list[str] = []
    deps = _make_deps([], outputs, tmp_data_file)
    out = action_book(Store(), deps)
    assert out == Store()
    assert any("No barbers available" in line for line in outputs)


def test_book_invalid_barber_selection(
    sample_store: Store, tmp_data_file: Path
) -> None:
    inputs = ["99"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    out = action_book(sample_store, deps)
    assert out == sample_store
    assert any("Invalid selection" in line for line in outputs)


def test_book_empty_client_name_rejected(
    sample_store: Store, tmp_data_file: Path
) -> None:
    inputs = [
        "1",
        "2026-06-01",
        "1",
        "1",
        "",
    ]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    out = action_book(sample_store, deps)
    assert out == sample_store
    assert any("Name cannot be empty" in line for line in outputs)


def test_book_no_slots_available(tmp_data_file: Path) -> None:
    """Picking a barber with no slots on the date aborts the flow."""
    from barber_booking.models import Barber, Booking, Store

    booked_alice = Booking(
        "Alice", "X", "2026-06-01", "09:00", "ts"
    )
    store = Store(
        barbers={
            "Alice": Barber("Alice", ("09:00",), {}, ""),
        },
        bookings=(booked_alice,),
    )
    inputs = ["1", "2026-06-01"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    assert action_book(store, deps) == store
    assert any("No available slots" in line for line in outputs)


# ── cancel ───────────────────────────────────────────────────────────


def test_cancel_confirmed(seeded_data_file: Path, sample_store: Store) -> None:
    inputs = ["1", "y"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, seeded_data_file)
    new_store = action_cancel(sample_store, deps)
    assert len(new_store.bookings) == 2


def test_cancel_aborted(seeded_data_file: Path, sample_store: Store) -> None:
    inputs = ["1", "n"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, seeded_data_file)
    out = action_cancel(sample_store, deps)
    assert out == sample_store
    assert any("aborted" in line.lower() for line in outputs)


def test_cancel_no_bookings(tmp_data_file: Path) -> None:
    outputs: list[str] = []
    deps = _make_deps([], outputs, tmp_data_file)
    out = action_cancel(Store(), deps)
    assert out == Store()


# ── reschedule ───────────────────────────────────────────────────────


def test_reschedule_happy_path(
    seeded_data_file: Path, sample_store: Store
) -> None:
    inputs = ["1", "2026-04-15", "1"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, seeded_data_file)
    new_store = action_reschedule(sample_store, deps)
    new_first = new_store.bookings[0]
    assert new_first.date == "2026-04-15"
    assert new_first.client == "Carol"


def test_reschedule_aborts_on_invalid_date(
    sample_store: Store, tmp_data_file: Path
) -> None:
    inputs = ["1", "not-a-date"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    out = action_reschedule(sample_store, deps)
    assert out == sample_store


# ── search ───────────────────────────────────────────────────────────


def test_search_hit(sample_store: Store, tmp_data_file: Path) -> None:
    inputs = ["alice"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    action_search(sample_store, deps)
    blob = "\n".join(outputs)
    assert "Found 2 booking(s)" in blob


def test_search_miss(sample_store: Store, tmp_data_file: Path) -> None:
    inputs = ["zoe"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    action_search(sample_store, deps)
    assert any("No bookings found matching" in line for line in outputs)


def test_search_empty_term(sample_store: Store, tmp_data_file: Path) -> None:
    inputs = [""]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    action_search(sample_store, deps)
    assert any("cannot be empty" in line for line in outputs)


# ── run loop ─────────────────────────────────────────────────────────


def test_run_exits_on_8(tmp_data_file: Path) -> None:
    inputs = ["8"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    run(deps)
    assert any("Goodbye" in line for line in outputs)


def test_run_invalid_then_exit(tmp_data_file: Path) -> None:
    inputs = ["999", "8"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, tmp_data_file)
    run(deps)
    assert any("Invalid option" in line for line in outputs)


def test_run_dispatches_list_barbers(
    seeded_data_file: Path, sample_store: Store
) -> None:
    inputs = ["2", "8"]
    outputs: list[str] = []
    deps = _make_deps(inputs, outputs, seeded_data_file)
    run(deps)
    blob = "\n".join(outputs)
    assert "Alice" in blob and "Goodbye" in blob


# ── notification integration with mocked SMTP ────────────────────────


def test_book_with_smtp_success_prints_email_sent(
    seeded_data_file: Path, sample_store: Store
) -> None:
    inputs = [
        "1",
        "2026-06-01",
        "1",
        "1",
        "Frank",
        "frank@example.com",
    ]
    outputs: list[str] = []

    full_env = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "u",
        "SMTP_PASS": "p",
    }
    deps = Deps(
        reader=lambda _p: inputs.pop(0),
        writer=outputs.append,
        now=lambda: datetime(2026, 5, 2, 10, 0, 0),
        env=full_env,
        data_file=str(seeded_data_file),
    )
    with mock.patch("barber_booking.notifications.smtplib.SMTP"):
        action_book(sample_store, deps)

    blob = "\n".join(outputs)
    assert "Email sent to: frank@example.com" in blob


def test_book_with_smtp_failure_prints_skipped(
    seeded_data_file: Path, sample_store: Store
) -> None:
    inputs = [
        "1",
        "2026-06-01",
        "1",
        "1",
        "Frank",
        "frank@example.com",
    ]
    outputs: list[str] = []
    full_env = {
        "SMTP_HOST": "smtp.example.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "u",
        "SMTP_PASS": "p",
    }
    deps = Deps(
        reader=lambda _p: inputs.pop(0),
        writer=outputs.append,
        now=lambda: datetime(2026, 5, 2, 10, 0, 0),
        env=full_env,
        data_file=str(seeded_data_file),
    )
    with mock.patch(
        "barber_booking.notifications.smtplib.SMTP", side_effect=OSError("boom")
    ):
        action_book(sample_store, deps)

    blob = "\n".join(outputs)
    assert "skipped - SMTP not configured or send failed" in blob
