"""Persistence operations for the case repository.

The routers stay thin: they translate HTTP into these calls and back. Anything
that touches the ORM lives here, which is what makes the seeder, the evaluator
and the API share one definition of "how a case is written".
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, Text, func, or_, select
from sqlalchemy.orm import Session, selectinload

from . import models, schemas


class CaseNotFoundError(LookupError):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"case {identifier!r} not found")
        self.identifier = identifier


class DuplicateCaseCodeError(ValueError):
    def __init__(self, case_code: str) -> None:
        super().__init__(f"case_code {case_code!r} already exists")
        self.case_code = case_code


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

_SORT_COLUMNS = {
    "case_code": models.Case.case_code,
    "title": models.Case.title,
    "difficulty": models.Case.difficulty,
    "updated_at": models.Case.updated_at,
    "created_at": models.Case.created_at,
    "discipline": models.Case.discipline,
}


def _full_case_stmt() -> Select[tuple[models.Case]]:
    return select(models.Case).options(
        selectinload(models.Case.lab_panels).selectinload(models.LabPanel.results),
        selectinload(models.Case.smears),
        selectinload(models.Case.microbiology),
        selectinload(models.Case.protocols),
        selectinload(models.Case.diagnoses),
        selectinload(models.Case.imaging),
    )


def _apply_filters(
    stmt: Select[Any],
    *,
    discipline: models.Discipline | None = None,
    subspecialty: str | None = None,
    status: models.CaseStatus | None = None,
    difficulty: int | None = None,
    difficulty_min: int | None = None,
    difficulty_max: int | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> Select[Any]:
    if discipline is not None:
        stmt = stmt.where(models.Case.discipline == discipline)
    if subspecialty:
        stmt = stmt.where(models.Case.subspecialty == subspecialty)
    if status is not None:
        stmt = stmt.where(models.Case.status == status)
    if difficulty is not None:
        stmt = stmt.where(models.Case.difficulty == difficulty)
    if difficulty_min is not None:
        stmt = stmt.where(models.Case.difficulty >= difficulty_min)
    if difficulty_max is not None:
        stmt = stmt.where(models.Case.difficulty <= difficulty_max)
    if search:
        needle = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(models.Case.title).like(needle),
                func.lower(models.Case.summary).like(needle),
                func.lower(models.Case.case_code).like(needle),
                func.lower(models.Case.subspecialty).like(needle),
            )
        )
    if tag:
        # JSON containment is dialect-specific; the tag list is tiny (<10 per
        # case) so a portable LIKE on the serialised array is both correct and
        # fast enough at this scale. Quoting prevents "ana" matching "anaemia".
        serialised = func.lower(func.cast(models.Case.tags, Text))
        stmt = stmt.where(serialised.like(f'%"{tag.lower()}"%'))
    return stmt


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def count_cases(db: Session, **filters: Any) -> int:
    stmt = _apply_filters(select(func.count(models.Case.id)), **filters)
    return int(db.execute(stmt).scalar_one())


def list_cases(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "case_code",
    sort_dir: str = "asc",
    **filters: Any,
) -> Sequence[models.Case]:
    column = _SORT_COLUMNS.get(sort_by, models.Case.case_code)
    order = column.desc() if sort_dir.lower() == "desc" else column.asc()
    stmt = _apply_filters(select(models.Case), **filters)
    stmt = stmt.order_by(order, models.Case.id.asc()).limit(limit).offset(offset)
    return db.execute(stmt).scalars().unique().all()


def get_case(db: Session, case_id: int) -> models.Case:
    stmt = _full_case_stmt().where(models.Case.id == case_id)
    case = db.execute(stmt).scalars().unique().one_or_none()
    if case is None:
        raise CaseNotFoundError(case_id)
    return case


def get_case_by_code(db: Session, case_code: str) -> models.Case:
    stmt = _full_case_stmt().where(models.Case.case_code == case_code.upper())
    case = db.execute(stmt).scalars().unique().one_or_none()
    if case is None:
        raise CaseNotFoundError(case_code)
    return case


def resolve_case(db: Session, identifier: str) -> models.Case:
    """Accept either a numeric id or a case code such as ``THY-001``."""
    if identifier.isdigit():
        return get_case(db, int(identifier))
    return get_case_by_code(db, identifier)


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def _build_children(case: models.Case, payload: dict[str, Any]) -> None:
    """Attach nested collections to ``case`` from a validated payload dict."""
    if (patient := payload.get("patient")) is not None:
        case.patient = models.Patient(**patient)
    if (presentation := payload.get("presentation")) is not None:
        case.presentation = models.Presentation(**presentation)

    for panel in payload.get("lab_panels") or []:
        results = panel.pop("results", [])
        panel_row = models.LabPanel(**panel)
        panel_row.results = [models.LabResult(**r) for r in results]
        case.lab_panels.append(panel_row)

    for smear in payload.get("smears") or []:
        case.smears.append(models.PeripheralSmear(**smear))
    for report in payload.get("microbiology") or []:
        case.microbiology.append(models.MicrobiologyReport(**report))
    for protocol in payload.get("protocols") or []:
        case.protocols.append(models.TreatmentProtocol(**protocol))
    for diagnosis in payload.get("diagnoses") or []:
        case.diagnoses.append(models.Diagnosis(**diagnosis))
    for study in payload.get("imaging") or []:
        case.imaging.append(models.ImagingStudy(**study))


_CHILD_KEYS = (
    "patient",
    "presentation",
    "lab_panels",
    "smears",
    "microbiology",
    "protocols",
    "diagnoses",
    "imaging",
)


def create_case(db: Session, payload: schemas.CaseCreate) -> models.Case:
    existing = db.execute(
        select(models.Case.id).where(models.Case.case_code == payload.case_code)
    ).scalar_one_or_none()
    if existing is not None:
        raise DuplicateCaseCodeError(payload.case_code)

    data = payload.model_dump()
    child_data = {key: data.pop(key, None) for key in _CHILD_KEYS}
    case = models.Case(**data)
    _build_children(case, child_data)
    db.add(case)
    db.flush()
    db.refresh(case)
    return case


def update_case(db: Session, case_id: int, payload: schemas.CaseUpdate) -> models.Case:
    case = get_case(db, case_id)
    data = payload.model_dump(exclude_unset=True)

    child_data = {key: data.pop(key) for key in _CHILD_KEYS if key in data}

    for field, value in data.items():
        setattr(case, field, value)

    # Replace-not-merge semantics for nested collections. A PATCH that omits
    # `lab_panels` leaves the timeline untouched; a PATCH that supplies it
    # replaces the whole timeline. Partial merging of a lab timeline has no
    # sane definition (what is the identity of a result?) so we refuse to
    # invent one.
    if "patient" in child_data and child_data["patient"] is not None:
        case.patient = models.Patient(**child_data["patient"])
    if "presentation" in child_data and child_data["presentation"] is not None:
        case.presentation = models.Presentation(**child_data["presentation"])
    if "lab_panels" in child_data and child_data["lab_panels"] is not None:
        case.lab_panels.clear()
        db.flush()
        for panel in child_data["lab_panels"]:
            results = panel.pop("results", [])
            row = models.LabPanel(**panel)
            row.results = [models.LabResult(**r) for r in results]
            case.lab_panels.append(row)
    for key, model_cls in (
        ("smears", models.PeripheralSmear),
        ("microbiology", models.MicrobiologyReport),
        ("protocols", models.TreatmentProtocol),
        ("diagnoses", models.Diagnosis),
        ("imaging", models.ImagingStudy),
    ):
        if key in child_data and child_data[key] is not None:
            collection = getattr(case, key)
            collection.clear()
            db.flush()
            for item in child_data[key]:
                collection.append(model_cls(**item))

    case.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(case)
    return case


def replace_case(db: Session, case_id: int, payload: schemas.CaseCreate) -> models.Case:
    """PUT semantics: the stored case becomes exactly the payload, keeping id."""
    case = get_case(db, case_id)
    if payload.case_code != case.case_code:
        clash = db.execute(
            select(models.Case.id).where(
                models.Case.case_code == payload.case_code, models.Case.id != case_id
            )
        ).scalar_one_or_none()
        if clash is not None:
            raise DuplicateCaseCodeError(payload.case_code)

    data = payload.model_dump()
    child_data = {key: data.pop(key, None) for key in _CHILD_KEYS}
    for field, value in data.items():
        setattr(case, field, value)

    case.patient = None
    case.presentation = None
    for key in ("lab_panels", "smears", "microbiology", "protocols", "diagnoses", "imaging"):
        getattr(case, key).clear()
    db.flush()

    _build_children(case, child_data)
    case.updated_at = datetime.now(UTC)
    db.flush()
    db.refresh(case)
    return case


def delete_case(db: Session, case_id: int) -> str:
    case = get_case(db, case_id)
    code = case.case_code
    db.delete(case)
    db.flush()
    return code


# ---------------------------------------------------------------------------
# Derived reads
# ---------------------------------------------------------------------------


def build_trends(
    db: Session, case: models.Case, analytes: Sequence[str] | None = None
) -> schemas.CaseTrendsRead:
    """Pivot the lab timeline into per-analyte series for the charts."""
    wanted = {a.upper() for a in analytes} if analytes else None
    intervals = {
        row.analyte_code: row
        for row in db.execute(select(models.ReferenceInterval)).scalars().all()
    }

    buckets: dict[str, schemas.AnalyteTrend] = {}
    for panel in sorted(case.lab_panels, key=lambda p: (p.day_offset, p.collected_at)):
        for result in panel.results:
            if result.value_numeric is None:
                continue  # qualitative results have no place on a line chart
            code = result.analyte_code.upper()
            if wanted is not None and code not in wanted:
                continue
            if code not in buckets:
                interval = intervals.get(code)
                buckets[code] = schemas.AnalyteTrend(
                    analyte_code=code,
                    analyte_name=result.analyte_name,
                    unit=result.unit,
                    ref_low=result.ref_low if result.ref_low is not None else getattr(interval, "ref_low", None),
                    ref_high=result.ref_high if result.ref_high is not None else getattr(interval, "ref_high", None),
                    critical_low=getattr(interval, "critical_low", None),
                    critical_high=getattr(interval, "critical_high", None),
                    decimals=getattr(interval, "decimals", 2),
                )
            buckets[code].points.append(
                schemas.TrendPoint(
                    collected_at=panel.collected_at,
                    day_offset=panel.day_offset,
                    value=result.value_numeric,
                    unit=result.unit,
                    flag=result.flag,
                    panel_code=panel.panel_code,
                    is_critical=result.is_critical,
                )
            )

    series = sorted(buckets.values(), key=lambda s: s.analyte_code)
    return schemas.CaseTrendsRead(case_id=case.id, case_code=case.case_code, series=series)


def compute_stats(db: Session) -> schemas.StatsResponse:
    def _group(column: Any) -> dict[str, int]:
        rows = db.execute(select(column, func.count(models.Case.id)).group_by(column)).all()
        out: dict[str, int] = {}
        for key, count in rows:
            out[key.value if hasattr(key, "value") else str(key)] = int(count)
        return out

    total = int(db.execute(select(func.count(models.Case.id))).scalar_one())
    panels = int(db.execute(select(func.count(models.LabPanel.id))).scalar_one())
    results = int(db.execute(select(func.count(models.LabResult.id))).scalar_one())

    return schemas.StatsResponse(
        total_cases=total,
        by_discipline=_group(models.Case.discipline),
        by_subspecialty=_group(models.Case.subspecialty),
        by_difficulty=_group(models.Case.difficulty),
        by_status=_group(models.Case.status),
        total_lab_results=results,
        total_panels=panels,
        generated_at=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Reference intervals + audit
# ---------------------------------------------------------------------------


def list_reference_intervals(
    db: Session, *, category: str | None = None, analyte: str | None = None
) -> Sequence[models.ReferenceInterval]:
    stmt = select(models.ReferenceInterval)
    if category:
        stmt = stmt.where(models.ReferenceInterval.category == category)
    if analyte:
        stmt = stmt.where(models.ReferenceInterval.analyte_code == analyte.upper())
    return db.execute(stmt.order_by(models.ReferenceInterval.analyte_code)).scalars().all()


def record_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    actor: str = "anonymous",
    request_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> models.AuditEvent:
    event = models.AuditEvent(
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        actor=actor,
        request_id=request_id,
        detail=detail or {},
    )
    db.add(event)
    db.flush()
    return event


def list_audit_events(db: Session, *, limit: int = 100) -> Sequence[models.AuditEvent]:
    stmt = select(models.AuditEvent).order_by(models.AuditEvent.occurred_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()
