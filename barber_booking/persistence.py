"""File I/O edge: load and save the :class:`Store` to JSON."""

from __future__ import annotations

import json
import os

from barber_booking.models import Store, empty_store, store_from_dict, store_to_dict

DEFAULT_DATA_FILE = "bookings.json"

__all__ = ["DEFAULT_DATA_FILE", "load_store", "save_store"]


def load_store(path: str = DEFAULT_DATA_FILE) -> Store:
    if not os.path.exists(path):
        return empty_store()
    with open(path, "r") as f:
        raw = json.load(f)
    return store_from_dict(raw)


def save_store(store: Store, path: str = DEFAULT_DATA_FILE) -> None:
    with open(path, "w") as f:
        json.dump(store_to_dict(store), f, indent=2)
