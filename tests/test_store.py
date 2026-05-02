"""Pure store-operation tests."""

from __future__ import annotations

import pytest

from barber_booking.models import Barber, Store, empty_store
from barber_booking.store import (
    add_barber,
    barber_email,
    get_barber,
    has_barber,
    list_barber_names,
)


def _make(name: str) -> Barber:
    return Barber(name=name, slots=(), services={}, email=f"{name.lower()}@x.com")


def test_add_barber_returns_new_store_without_mutating_input() -> None:
    store = empty_store()
    b = _make("Alice")
    new_store = add_barber(store, b)
    assert new_store is not store
    assert "Alice" in new_store.barbers
    assert "Alice" not in store.barbers


def test_add_barber_rejects_duplicate(sample_store: Store) -> None:
    with pytest.raises(ValueError, match="already registered"):
        add_barber(sample_store, _make("Alice"))


def test_has_and_get_barber(sample_store: Store) -> None:
    assert has_barber(sample_store, "Alice") is True
    assert has_barber(sample_store, "Zoe") is False
    assert get_barber(sample_store, "Alice") is sample_store.barbers["Alice"]
    assert get_barber(sample_store, "Zoe") is None


def test_barber_email_unknown_returns_empty(sample_store: Store) -> None:
    assert barber_email(sample_store, "Zoe") == ""
    assert barber_email(sample_store, "Alice") == "alice@example.com"


def test_list_barber_names_preserves_insertion_order() -> None:
    s = empty_store()
    s = add_barber(s, _make("Alice"))
    s = add_barber(s, _make("Bob"))
    s = add_barber(s, _make("Carol"))
    assert list_barber_names(s) == ["Alice", "Bob", "Carol"]
