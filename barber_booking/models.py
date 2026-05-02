"""Domain models and (de)serialization for the barber booking agent.

Defines frozen dataclasses for in-memory state and TypedDicts mirroring the
on-disk JSON shape (`bookings.json`). All conversion between them is isolated
to this module so the rest of the codebase can stay typed and immutable.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Mapping, TypedDict


class BarberDict(TypedDict):
    slots: list[str]
    services: dict[str, float]
    email: str


class BookingDict(TypedDict, total=False):
    barber: str
    client: str
    client_email: str
    date: str
    time: str
    service: str | None
    price: float
    booked_at: str


class StoreDict(TypedDict):
    barbers: dict[str, BarberDict]
    bookings: list[BookingDict]


@dataclass(frozen=True)
class Barber:
    name: str
    slots: tuple[str, ...]
    services: Mapping[str, float]
    email: str = ""


@dataclass(frozen=True)
class Booking:
    barber: str
    client: str
    date: str
    time: str
    booked_at: str
    client_email: str = ""
    service: str | None = None
    price: float = 0.0


@dataclass(frozen=True)
class Store:
    barbers: Mapping[str, Barber] = field(default_factory=dict)
    bookings: tuple[Booking, ...] = ()


@dataclass(frozen=True)
class NewBarber:
    name: str
    email: str
    slots: tuple[str, ...]
    services: Mapping[str, float]


@dataclass(frozen=True)
class NewBooking:
    barber: str
    client: str
    client_email: str
    date: str
    time: str
    service: str | None
    price: float


def barber_from_dict(name: str, d: BarberDict) -> Barber:
    return Barber(
        name=name,
        slots=tuple(d.get("slots", [])),
        services=dict(d.get("services", {})),
        email=d.get("email", ""),
    )


def barber_to_dict(b: Barber) -> BarberDict:
    return {
        "slots": list(b.slots),
        "services": dict(b.services),
        "email": b.email,
    }


def booking_from_dict(d: BookingDict) -> Booking:
    return Booking(
        barber=d["barber"],
        client=d["client"],
        client_email=d.get("client_email", ""),
        date=d["date"],
        time=d["time"],
        service=d.get("service"),
        price=float(d.get("price", 0.0)),
        booked_at=d.get("booked_at", ""),
    )


def booking_to_dict(b: Booking) -> BookingDict:
    return {
        "barber": b.barber,
        "client": b.client,
        "client_email": b.client_email,
        "date": b.date,
        "time": b.time,
        "service": b.service,
        "price": b.price,
        "booked_at": b.booked_at,
    }


def store_from_dict(d: StoreDict) -> Store:
    barbers = {
        name: barber_from_dict(name, bd) for name, bd in d.get("barbers", {}).items()
    }
    bookings = tuple(booking_from_dict(b) for b in d.get("bookings", []))
    return Store(barbers=barbers, bookings=bookings)


def store_to_dict(s: Store) -> StoreDict:
    return {
        "barbers": {name: barber_to_dict(b) for name, b in s.barbers.items()},
        "bookings": [booking_to_dict(b) for b in s.bookings],
    }


def empty_store() -> Store:
    return Store(barbers={}, bookings=())


def with_barbers(store: Store, barbers: Mapping[str, Barber]) -> Store:
    return replace(store, barbers=dict(barbers))


def with_bookings(store: Store, bookings: tuple[Booking, ...]) -> Store:
    return replace(store, bookings=bookings)
