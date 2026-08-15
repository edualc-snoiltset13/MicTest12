"""Pytest fixtures.

Each test module gets a fresh, file-backed SQLite database seeded from the real
JSON corpus. A file rather than ``:memory:`` is used because the seeder opens
its own sessions, and because the corpus load (~0.5 s) is cheap enough to pay
once per session while keeping the tests honest about the real data.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def _isolated_database() -> Iterator[None]:
    tmpdir = tempfile.mkdtemp(prefix="medsim-tests-")
    db_path = Path(tmpdir) / "test.db"
    os.environ["MEDSIM_DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["MEDSIM_ENVIRONMENT"] = "test"
    os.environ["MEDSIM_AUTO_SEED"] = "true"
    os.environ["MEDSIM_CHAOS_ENABLED"] = "true"  # exercised by the chaos tests
    os.environ["MEDSIM_LOG_LEVEL"] = "WARNING"

    from app.config import reset_settings_cache
    from app.database import dispose_engine

    reset_settings_cache()
    dispose_engine()
    yield
    dispose_engine()


@pytest.fixture(scope="session")
def client(_isolated_database: None):  # type: ignore[no-untyped-def]
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:  # triggers lifespan -> create_all + seed
        yield test_client


@pytest.fixture()
def db_session():  # type: ignore[no-untyped-def]
    from app.database import session_scope

    with session_scope() as session:
        yield session


@pytest.fixture()
def sample_case_payload() -> dict:
    """A minimal but valid CaseCreate payload used by the write-path tests."""
    return {
        "case_code": "TST-001",
        "title": "Synthetic test case for CRUD verification",
        "title_i18n": {"en": "Synthetic test case", "de": "Synthetischer Testfall"},
        "summary": "Created by the test-suite.",
        "discipline": "chemical_pathology",
        "subspecialty": "thyroid",
        "difficulty": 2,
        "tags": ["test", "synthetic"],
        "patient": {"pseudonym": "Test Patient", "age_years": 40, "sex": "female"},
        "presentation": {"chief_complaint": "Test complaint"},
        "lab_panels": [
            {
                "panel_code": "TFT",
                "panel_name": "Thyroid function tests",
                "collected_at": "2026-01-06T08:00:00Z",
                "day_offset": 0,
                "results": [
                    {
                        "analyte_code": "TSH",
                        "analyte_name": "Thyroid-stimulating hormone",
                        "value_numeric": 12.4,
                        "unit": "mIU/L",
                        "ref_low": 0.4,
                        "ref_high": 4.0,
                        "flag": "H",
                    }
                ],
            }
        ],
        "diagnoses": [
            {"label": "Test diagnosis", "is_primary": True, "certainty": "confirmed"}
        ],
    }
