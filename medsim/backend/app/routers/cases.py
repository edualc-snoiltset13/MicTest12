"""Case CRUD + derived-read endpoints.

Route map (mounted under ``/api/v1``)::

    GET    /cases                    list + filter + paginate (summary projection)
    POST   /cases                    create a full case aggregate
    GET    /cases/stats              corpus statistics
    GET    /cases/export             bulk export of every case (seed-file shape)
    GET    /cases/{identifier}       fetch by numeric id or case code
    PUT    /cases/{identifier}       full replace
    PATCH  /cases/{identifier}       partial update (replace-not-merge on lists)
    DELETE /cases/{identifier}       delete (cascades to all children)
    GET    /cases/{identifier}/trends       per-analyte time series for charts
    GET    /cases/{identifier}/labs         lab timeline only
    GET    /cases/{identifier}/smears       peripheral blood smears only
    GET    /cases/{identifier}/microbiology microbiology reports only
    GET    /cases/{identifier}/protocols    treatment protocols only
    GET    /cases/{identifier}/diagnoses    diagnosis + differential only

Ordering matters: ``/cases/stats`` and ``/cases/export`` are declared before
``/cases/{identifier}`` so the literal paths win over the path parameter.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/cases", tags=["cases"])

DbSession = Annotated[Session, Depends(get_db)]


def _actor(request: Request) -> str:
    """Best-effort actor identity for the audit trail.

    Authentication is out of scope for the simulation corpus (all content is
    synthetic), so we record the caller-declared identity and the request id
    rather than pretending to have an authenticated principal.
    """
    return request.headers.get("X-Actor", "anonymous")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _resolve(db: Session, identifier: str) -> models.Case:
    try:
        return crud.resolve_case(db, identifier)
    except crud.CaseNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No case matching {identifier!r}.",
        ) from exc


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=schemas.CaseListResponse,
    summary="List case studies",
    response_description="Paginated case summaries with filter metadata",
)
def list_cases(
    db: DbSession,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    discipline: models.Discipline | None = None,
    subspecialty: Annotated[str | None, Query(max_length=64)] = None,
    case_status: Annotated[models.CaseStatus | None, Query(alias="status")] = None,
    difficulty: Annotated[int | None, Query(ge=1, le=5)] = None,
    difficulty_min: Annotated[int | None, Query(ge=1, le=5)] = None,
    difficulty_max: Annotated[int | None, Query(ge=1, le=5)] = None,
    tag: Annotated[str | None, Query(max_length=64)] = None,
    search: Annotated[str | None, Query(max_length=128)] = None,
    sort_by: schemas.SortField = "case_code",
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
) -> schemas.CaseListResponse:
    if difficulty_min is not None and difficulty_max is not None and difficulty_min > difficulty_max:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="difficulty_min must not exceed difficulty_max.",
        )

    filters: dict[str, Any] = {
        "discipline": discipline,
        "subspecialty": subspecialty,
        "status": case_status,
        "difficulty": difficulty,
        "difficulty_min": difficulty_min,
        "difficulty_max": difficulty_max,
        "tag": tag,
        "search": search,
    }
    total = crud.count_cases(db, **filters)
    rows = crud.list_cases(
        db, limit=limit, offset=offset, sort_by=sort_by, sort_dir=sort_dir, **filters
    )
    items = [schemas.CaseSummaryRead.model_validate(row) for row in rows]
    meta = schemas.PageMeta(
        total=total,
        limit=limit,
        offset=offset,
        returned=len(items),
        has_more=offset + len(items) < total,
    )
    response.headers["X-Total-Count"] = str(total)
    return schemas.CaseListResponse(meta=meta, items=items)


@router.post(
    "",
    response_model=schemas.CaseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a case study",
)
def create_case(
    payload: schemas.CaseCreate, db: DbSession, request: Request, response: Response
) -> models.Case:
    try:
        case = crud.create_case(db, payload)
    except crud.DuplicateCaseCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Case code {exc.case_code} is already in use.",
        ) from exc

    crud.record_audit(
        db,
        action="create",
        entity_type="case",
        entity_id=case.case_code,
        actor=_actor(request),
        request_id=_request_id(request),
        detail={"title": case.title, "discipline": case.discipline.value},
    )
    response.headers["Location"] = f"{request.url.path.rstrip('/')}/{case.case_code}"
    return case


@router.get("/stats", response_model=schemas.StatsResponse, summary="Corpus statistics")
def case_stats(db: DbSession) -> schemas.StatsResponse:
    return crud.compute_stats(db)


@router.get(
    "/export",
    response_model=list[schemas.CaseRead],
    summary="Export every case in seed-file shape",
)
def export_cases(db: DbSession) -> list[models.Case]:
    rows = crud.list_cases(db, limit=1000, offset=0)
    return [crud.get_case(db, row.id) for row in rows]


# ---------------------------------------------------------------------------
# Item
# ---------------------------------------------------------------------------


@router.get(
    "/{identifier}",
    response_model=schemas.CaseRead,
    summary="Fetch one case by id or case code",
)
def get_case(identifier: str, db: DbSession) -> models.Case:
    return _resolve(db, identifier)


@router.put("/{identifier}", response_model=schemas.CaseRead, summary="Replace a case")
def replace_case(
    identifier: str, payload: schemas.CaseCreate, db: DbSession, request: Request
) -> models.Case:
    case = _resolve(db, identifier)
    try:
        updated = crud.replace_case(db, case.id, payload)
    except crud.DuplicateCaseCodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Case code {exc.case_code} is already in use.",
        ) from exc
    crud.record_audit(
        db,
        action="replace",
        entity_type="case",
        entity_id=updated.case_code,
        actor=_actor(request),
        request_id=_request_id(request),
    )
    return updated


@router.patch("/{identifier}", response_model=schemas.CaseRead, summary="Update a case")
def update_case(
    identifier: str, payload: schemas.CaseUpdate, db: DbSession, request: Request
) -> models.Case:
    case = _resolve(db, identifier)
    if not payload.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="PATCH body contained no updatable fields.",
        )
    updated = crud.update_case(db, case.id, payload)
    crud.record_audit(
        db,
        action="update",
        entity_type="case",
        entity_id=updated.case_code,
        actor=_actor(request),
        request_id=_request_id(request),
        detail={"fields": sorted(payload.model_dump(exclude_unset=True).keys())},
    )
    return updated


@router.delete(
    "/{identifier}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a case"
)
def delete_case(identifier: str, db: DbSession, request: Request) -> Response:
    case = _resolve(db, identifier)
    code = crud.delete_case(db, case.id)
    crud.record_audit(
        db,
        action="delete",
        entity_type="case",
        entity_id=code,
        actor=_actor(request),
        request_id=_request_id(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Sub-resources
# ---------------------------------------------------------------------------


@router.get(
    "/{identifier}/trends",
    response_model=schemas.CaseTrendsRead,
    summary="Per-analyte time series for charting",
)
def case_trends(
    identifier: str,
    db: DbSession,
    analytes: Annotated[
        list[str] | None,
        Query(description="Repeatable analyte code filter, e.g. ?analytes=TSH&analytes=FT4"),
    ] = None,
) -> schemas.CaseTrendsRead:
    case = _resolve(db, identifier)
    return crud.build_trends(db, case, analytes)


@router.get(
    "/{identifier}/labs",
    response_model=list[schemas.LabPanelRead],
    summary="Lab timeline for a case",
)
def case_labs(
    identifier: str,
    db: DbSession,
    panel_code: Annotated[str | None, Query(max_length=64)] = None,
) -> list[models.LabPanel]:
    case = _resolve(db, identifier)
    panels = sorted(case.lab_panels, key=lambda p: (p.day_offset, p.collected_at))
    if panel_code:
        panels = [p for p in panels if p.panel_code.lower() == panel_code.lower()]
    return panels


@router.get(
    "/{identifier}/smears",
    response_model=list[schemas.PeripheralSmearRead],
    summary="Peripheral blood smear reports",
)
def case_smears(identifier: str, db: DbSession) -> list[models.PeripheralSmear]:
    return sorted(_resolve(db, identifier).smears, key=lambda s: s.day_offset)


@router.get(
    "/{identifier}/microbiology",
    response_model=list[schemas.MicrobiologyReportRead],
    summary="Microbiology reports",
)
def case_microbiology(identifier: str, db: DbSession) -> list[models.MicrobiologyReport]:
    return sorted(_resolve(db, identifier).microbiology, key=lambda m: m.day_offset)


@router.get(
    "/{identifier}/protocols",
    response_model=list[schemas.TreatmentProtocolRead],
    summary="Treatment protocols",
)
def case_protocols(identifier: str, db: DbSession) -> list[models.TreatmentProtocol]:
    return _resolve(db, identifier).protocols


@router.get(
    "/{identifier}/diagnoses",
    response_model=list[schemas.DiagnosisRead],
    summary="Primary diagnosis and differential",
)
def case_diagnoses(identifier: str, db: DbSession) -> list[models.Diagnosis]:
    diagnoses = _resolve(db, identifier).diagnoses
    # Primary first, then by descending likelihood so the differential renders
    # in the order a clinician would work through it.
    return sorted(diagnoses, key=lambda d: (not d.is_primary, -(d.likelihood or 0.0)))
