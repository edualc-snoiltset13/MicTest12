"""Pure operations on a :class:`Store` of barbers."""

from __future__ import annotations

from barber_booking.models import Barber, Store, empty_store, with_barbers

__all__ = [
    "empty_store",
    "has_barber",
    "get_barber",
    "add_barber",
    "barber_email",
    "list_barber_names",
]


def has_barber(store: Store, name: str) -> bool:
    return name in store.barbers


def get_barber(store: Store, name: str) -> Barber | None:
    return store.barbers.get(name)


def add_barber(store: Store, b: Barber) -> Store:
    if b.name in store.barbers:
        raise ValueError(f"Barber '{b.name}' is already registered.")
    new_barbers = dict(store.barbers)
    new_barbers[b.name] = b
    return with_barbers(store, new_barbers)


def barber_email(store: Store, name: str) -> str:
    b = store.barbers.get(name)
    return b.email if b else ""


def list_barber_names(store: Store) -> list[str]:
    return list(store.barbers.keys())
