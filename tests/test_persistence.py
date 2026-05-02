"""Persistence (file I/O) tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from barber_booking.models import Store, store_to_dict
from barber_booking.persistence import load_store, save_store


def test_load_missing_file_returns_empty_store(tmp_data_file: Path) -> None:
    s = load_store(str(tmp_data_file))
    assert s == Store(barbers={}, bookings=())


def test_save_then_load_round_trips(
    tmp_data_file: Path, sample_store: Store
) -> None:
    save_store(sample_store, str(tmp_data_file))
    loaded = load_store(str(tmp_data_file))
    assert loaded == sample_store


def test_saved_json_matches_legacy_schema(
    tmp_data_file: Path, sample_store: Store
) -> None:
    save_store(sample_store, str(tmp_data_file))
    raw = json.loads(tmp_data_file.read_text())
    assert set(raw.keys()) == {"barbers", "bookings"}
    alice = raw["barbers"]["Alice"]
    assert set(alice.keys()) == {"slots", "services", "email"}
    booking = raw["bookings"][0]
    assert set(booking.keys()) >= {
        "barber",
        "client",
        "client_email",
        "date",
        "time",
        "service",
        "price",
        "booked_at",
    }


def test_byte_equivalent_resave(
    tmp_data_file: Path, sample_store: Store
) -> None:
    save_store(sample_store, str(tmp_data_file))
    first = tmp_data_file.read_bytes()
    loaded = load_store(str(tmp_data_file))
    save_store(loaded, str(tmp_data_file))
    assert tmp_data_file.read_bytes() == first


def test_saved_uses_indent_two(tmp_data_file: Path, sample_store: Store) -> None:
    save_store(sample_store, str(tmp_data_file))
    text = tmp_data_file.read_text()
    assert "\n  " in text


def test_load_corrupt_json_raises_documents_latent_bug(tmp_data_file: Path) -> None:
    """LATENT: corrupt JSON propagates :class:`json.JSONDecodeError`.

    The original implementation has the same behavior; this test pins it down
    so a future fix has to update the test deliberately.
    """
    tmp_data_file.write_text("{not valid json")
    with pytest.raises(json.JSONDecodeError):
        load_store(str(tmp_data_file))


def test_round_trip_preserves_dict_returned_shape(
    tmp_data_file: Path, sample_store: Store
) -> None:
    save_store(sample_store, str(tmp_data_file))
    raw = json.loads(tmp_data_file.read_text())
    assert raw == store_to_dict(sample_store)
