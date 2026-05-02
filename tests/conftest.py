"""Shared fixtures for the barber booking test suite."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator

import pytest

from barber_booking.cli import Deps
from barber_booking.models import Barber, Booking, Store
from barber_booking.persistence import save_store


@pytest.fixture
def sample_store() -> Store:
    barbers = {
        "Alice": Barber(
            name="Alice",
            slots=("09:00", "10:00", "11:00"),
            services={"Haircut": 25.0, "Shave": 15.0},
            email="alice@example.com",
        ),
        "Bob": Barber(
            name="Bob",
            slots=("13:00", "14:00"),
            services={},
            email="",
        ),
    }
    bookings = (
        Booking(
            barber="Alice",
            client="Carol",
            client_email="carol@example.com",
            date="2026-04-01",
            time="09:00",
            booked_at="2026-03-30T12:00:00",
            service="Haircut",
            price=25.0,
        ),
        Booking(
            barber="Alice",
            client="Dan",
            client_email="",
            date="2026-05-10",
            time="10:00",
            booked_at="2026-04-25T08:00:00",
            service=None,
            price=0.0,
        ),
        Booking(
            barber="Bob",
            client="Eve",
            client_email="eve@example.com",
            date="2026-05-10",
            time="13:00",
            booked_at="2026-04-25T09:00:00",
            service=None,
            price=0.0,
        ),
    )
    return Store(barbers=barbers, bookings=bookings)


@pytest.fixture
def tmp_data_file(tmp_path: Path) -> Path:
    return tmp_path / "bookings.json"


@pytest.fixture
def fixed_now() -> Callable[[], datetime]:
    target = datetime(2026, 5, 2, 10, 0, 0)
    return lambda: target


@pytest.fixture
def fake_io() -> Iterator[tuple[list[str], list[str], Callable[[str], str], Callable[[str], None]]]:
    """Returns ``(inputs, outputs, reader, writer)``.

    Tests append answers to ``inputs`` *before* invoking the function under
    test. ``outputs`` collects every line passed to ``writer``.
    """
    inputs: list[str] = []
    outputs: list[str] = []

    def reader(_prompt: str) -> str:
        if not inputs:
            raise AssertionError("reader called but no inputs queued")
        return inputs.pop(0)

    def writer(line: str) -> None:
        outputs.append(line)

    yield inputs, outputs, reader, writer


@pytest.fixture
def deps_for(
    tmp_data_file: Path,
    fixed_now: Callable[[], datetime],
    fake_io: tuple[list[str], list[str], Callable[[str], str], Callable[[str], None]],
) -> Deps:
    inputs, outputs, reader, writer = fake_io
    return Deps(
        reader=reader,
        writer=writer,
        now=fixed_now,
        env={},
        data_file=str(tmp_data_file),
    )


@pytest.fixture
def seeded_data_file(tmp_data_file: Path, sample_store: Store) -> Path:
    save_store(sample_store, str(tmp_data_file))
    return tmp_data_file
