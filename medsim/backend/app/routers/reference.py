"""Reference-interval and metadata endpoints.

The frontend needs these to shade the "normal band" on every chart and to know
how many decimal places an analyte is conventionally reported to (TSH to two,
haemoglobin to one, bacterial index to one). Shipping that as data rather than
hardcoding it in the chart component is what lets a lab swap in its own
intervals without a frontend release.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/reference", tags=["reference"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/intervals",
    response_model=list[schemas.ReferenceIntervalRead],
    summary="List analyte reference intervals",
)
def list_intervals(
    db: DbSession,
    category: Annotated[str | None, Query(max_length=64)] = None,
    analyte: Annotated[str | None, Query(max_length=64)] = None,
) -> list[models.ReferenceInterval]:
    return list(crud.list_reference_intervals(db, category=category, analyte=analyte))


@router.get(
    "/intervals/{analyte_code}",
    response_model=schemas.ReferenceIntervalRead,
    summary="Fetch one analyte's reference interval",
)
def get_interval(analyte_code: str, db: DbSession) -> models.ReferenceInterval:
    rows = crud.list_reference_intervals(db, analyte=analyte_code)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No reference interval registered for analyte {analyte_code!r}.",
        )
    return rows[0]


@router.get("/enums", summary="Enumerations used across the API")
def list_enums() -> dict[str, list[str]]:
    """Single source of truth for dropdown contents in the dashboard.

    The frontend renders filter dropdowns from this, so adding a discipline
    server-side does not require a frontend change.
    """
    return {
        "disciplines": [d.value for d in models.Discipline],
        "statuses": [s.value for s in models.CaseStatus],
        "sexes": [s.value for s in models.Sex],
        "flags": [f.value for f in models.ResultFlag],
        "certainties": [c.value for c in models.Certainty],
        "locales": list(schemas.SUPPORTED_LOCALES),
    }


@router.get("/audit", summary="Recent audit events")
def list_audit(
    db: DbSession, limit: Annotated[int, Query(ge=1, le=500)] = 100
) -> list[dict]:
    events = crud.list_audit_events(db, limit=limit)
    return [
        {
            "id": e.id,
            "occurred_at": e.occurred_at.isoformat(),
            "actor": e.actor,
            "action": e.action,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "request_id": e.request_id,
            "detail": e.detail,
        }
        for e in events
    ]
