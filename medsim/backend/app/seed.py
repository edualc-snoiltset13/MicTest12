"""Seed loader for the case corpus and reference intervals.

The JSON seed files are the authoritative source of clinical content; the
database is a queryable projection of them. That direction matters: a reviewer
diffs a pull request against readable JSON, not against SQL INSERTs.

Compactness trick: seed files carry a per-case ``index_date`` plus integer
``day_offset`` values instead of a full timestamp on every panel. The loader
expands those into absolute timestamps. Writing 40 ISO-8601 strings per case by
hand is how timelines end up internally inconsistent.

Usage::

    python -m app.seed                # load if empty
    python -m app.seed --force        # wipe and reload
    python -m app.seed --validate     # parse and validate without writing
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from . import models, schemas
from .config import get_settings
from .database import create_all, session_scope

DEFAULT_INDEX_DATE = datetime(2026, 1, 6, 8, 0, tzinfo=UTC)

# Hour-of-day assigned per panel index within a single day, so that two panels
# drawn on the same day sort deterministically and render as distinct points.
_PANEL_HOURS = (8, 11, 14, 17, 20, 23)


@dataclass
class SeedReport:
    cases_loaded: int = 0
    intervals_loaded: int = 0
    reseeded: bool = False
    files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# ---------------------------------------------------------------------------
# Loading + normalisation
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.name}: invalid JSON at line {exc.lineno}: {exc.msg}") from exc


def _parse_index_date(raw: str | None) -> datetime:
    if not raw:
        return DEFAULT_INDEX_DATE
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _expand_timestamps(case: dict[str, Any], index_date: datetime) -> dict[str, Any]:
    """Turn ``day_offset`` into absolute ``collected_at`` values in place."""
    seen_per_day: dict[int, int] = {}

    def stamp(entry: dict[str, Any]) -> None:
        if entry.get("collected_at"):
            return
        offset = int(entry.get("day_offset", 0))
        n = seen_per_day.get(offset, 0)
        seen_per_day[offset] = n + 1
        hour = _PANEL_HOURS[min(n, len(_PANEL_HOURS) - 1)]
        entry["collected_at"] = (
            index_date + timedelta(days=offset)
        ).replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()

    for panel in case.get("lab_panels", []):
        stamp(panel)
    seen_per_day.clear()
    for smear in case.get("smears", []):
        stamp(smear)
    seen_per_day.clear()
    for report in case.get("microbiology", []):
        stamp(report)
    return case


def _autoflag(case: dict[str, Any]) -> dict[str, Any]:
    """Fill in a result ``flag`` when the seed file omits it.

    Authors write flags explicitly where the interpretation is subtle (a "normal"
    TSH that is inappropriate for a low FT4, for example, is deliberately left
    as ``N`` so the learner has to notice it). Where the flag is mechanical, we
    derive it, which removes a whole class of copy-paste error from the corpus.
    """
    for panel in case.get("lab_panels", []):
        for result in panel.get("results", []):
            if "flag" in result:
                continue
            value = result.get("value_numeric")
            low, high = result.get("ref_low"), result.get("ref_high")
            if value is None or (low is None and high is None):
                result["flag"] = "N"
                continue
            if high is not None and value > high:
                result["flag"] = "H"
            elif low is not None and value < low:
                result["flag"] = "L"
            else:
                result["flag"] = "N"
    return case


def load_case_files(data_dir: Path) -> tuple[list[schemas.CaseCreate], list[str], list[str]]:
    """Parse every ``cases_*.json`` file under ``data_dir``.

    Returns (validated cases, filenames read, error strings).
    """
    cases: list[schemas.CaseCreate] = []
    filenames: list[str] = []
    errors: list[str] = []

    for path in sorted(data_dir.glob("cases_*.json")):
        filenames.append(path.name)
        try:
            document = _read_json(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        file_index_date = _parse_index_date(document.get("index_date"))
        for raw_case in document.get("cases", []):
            code = raw_case.get("case_code", "<unknown>")
            index_date = _parse_index_date(raw_case.get("index_date")) if raw_case.get(
                "index_date"
            ) else file_index_date
            raw_case = _expand_timestamps(dict(raw_case), index_date)
            raw_case = _autoflag(raw_case)
            raw_case.pop("index_date", None)
            try:
                cases.append(schemas.CaseCreate.model_validate(raw_case))
            except ValidationError as exc:
                for err in exc.errors():
                    loc = ".".join(str(p) for p in err["loc"])
                    errors.append(f"{path.name} [{code}] {loc}: {err['msg']}")

    duplicates = _duplicate_codes([c.case_code for c in cases])
    errors.extend(f"duplicate case_code: {code}" for code in duplicates)
    return cases, filenames, errors


def _duplicate_codes(codes: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for code in codes:
        if code in seen:
            dupes.add(code)
        seen.add(code)
    return sorted(dupes)


def load_reference_intervals(data_dir: Path) -> list[dict[str, Any]]:
    path = data_dir / "reference_intervals.json"
    if not path.exists():
        return []
    document = _read_json(path)
    return document.get("intervals", [])


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def _wipe(db: Session) -> None:
    # Children cascade from cases, but reference intervals and audit rows are
    # independent tables and must be cleared explicitly.
    db.execute(delete(models.ReferenceInterval))
    for case in db.execute(select(models.Case)).scalars().all():
        db.delete(case)
    db.flush()


def seed_database(*, force: bool = False, data_dir: Path | None = None) -> SeedReport:
    settings = get_settings()
    data_dir = data_dir or settings.data_dir
    report = SeedReport()

    if not data_dir.exists():
        report.errors.append(f"data directory not found: {data_dir}")
        return report

    cases, filenames, errors = load_case_files(data_dir)
    report.files = filenames
    report.errors.extend(errors)
    intervals = load_reference_intervals(data_dir)

    if report.errors:
        # Refuse to load a partially-valid corpus: a dashboard showing 19 of 25
        # cases with no error is worse than one that fails loudly at boot.
        return report

    create_all()
    with session_scope() as db:
        existing = int(db.execute(select(func.count(models.Case.id))).scalar_one())
        if existing and not force:
            report.cases_loaded = existing
            report.intervals_loaded = int(
                db.execute(select(func.count(models.ReferenceInterval.id))).scalar_one()
            )
            return report

        if existing:
            _wipe(db)
            report.reseeded = True

        from . import crud

        for case in cases:
            crud.create_case(db, case)
        report.cases_loaded = len(cases)

        for interval in intervals:
            db.add(models.ReferenceInterval(**interval))
        report.intervals_loaded = len(intervals)

    return report


def validate_only(data_dir: Path | None = None) -> SeedReport:
    settings = get_settings()
    data_dir = data_dir or settings.data_dir
    report = SeedReport()
    cases, filenames, errors = load_case_files(data_dir)
    report.files = filenames
    report.errors = errors
    report.cases_loaded = len(cases)
    report.intervals_loaded = len(load_reference_intervals(data_dir))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the MedSimQA case database.")
    parser.add_argument("--force", action="store_true", help="wipe existing data and reload")
    parser.add_argument("--validate", action="store_true", help="validate seed files only")
    parser.add_argument("--data-dir", type=Path, default=None, help="override the seed directory")
    args = parser.parse_args(argv)

    report = validate_only(args.data_dir) if args.validate else seed_database(
        force=args.force, data_dir=args.data_dir
    )

    print(f"files       : {', '.join(report.files) or '(none)'}")
    print(f"cases       : {report.cases_loaded}")
    print(f"intervals   : {report.intervals_loaded}")
    print(f"reseeded    : {report.reseeded}")
    if report.errors:
        print(f"\n{len(report.errors)} error(s):", file=sys.stderr)
        for error in report.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("status      : ok")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
