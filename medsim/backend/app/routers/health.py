"""Liveness/readiness endpoints.

``/healthz`` is the systemd + load-balancer liveness probe: it must never touch
the database, or a slow query takes the process down. ``/readyz`` is the
readiness probe and *does* check the database, because a service that cannot
reach its data should be pulled from rotation without being restarted.
"""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import Settings, get_settings
from ..database import get_db

router = APIRouter(tags=["health"])

_BOOT_TIME = time.time()

DbSession = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/healthz", summary="Liveness probe")
def healthz(settings: SettingsDep) -> dict[str, object]:
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - _BOOT_TIME, 3),
    }


@router.get(
    "/readyz",
    response_model=schemas.HealthResponse,
    summary="Readiness probe (checks database connectivity and seed state)",
)
def readyz(db: DbSession, settings: SettingsDep, response: Response) -> schemas.HealthResponse:
    checks: dict[str, str] = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
        db_state = "connected"
    except Exception as exc:  # pragma: no cover - only on a broken DB
        checks["database"] = f"error: {exc.__class__.__name__}"
        db_state = "unavailable"

    case_count = 0
    if db_state == "connected":
        case_count = int(db.execute(select(func.count(models.Case.id))).scalar_one())
        checks["seed"] = "ok" if case_count >= 25 else f"degraded: only {case_count} cases"

    checks["chaos"] = "enabled" if settings.chaos_enabled else "disabled"

    if db_state != "connected":
        state: str = "error"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif case_count < 25:
        state = "degraded"
    else:
        state = "ok"

    return schemas.HealthResponse(
        status=state,  # type: ignore[arg-type]
        version=settings.app_version,
        environment=settings.environment,
        database=db_state,
        case_count=case_count,
        uptime_seconds=round(time.time() - _BOOT_TIME, 3),
        checks=checks,
    )
