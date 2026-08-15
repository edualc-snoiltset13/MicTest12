"""MedSimQA FastAPI application factory and entrypoint.

Run locally with::

    uvicorn app.main:app --reload --port 8000

The app is built by a factory so that the test-suite can construct isolated
instances with overridden settings instead of mutating a module-level global.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings, get_settings
from .database import create_all
from .middleware import (
    ChaosMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
    connection_reset_handler,
)
from .routers import cases, evaluation, health, reference
from .schemas import ErrorDetail

logger = logging.getLogger("medsim")

API_DESCRIPTION = """
**MedSimQA** is a medical diagnosis simulation and QA testing framework.

It serves a curated corpus of synthetic-but-clinically-faithful case studies
across four disciplines — chemical pathology, haematology, microbiology and
pharmacology — together with the reference intervals, treatment protocols and
grading keys needed to evaluate clinical reasoning, whether human or machine.

### Content warning
Every patient in this corpus is **synthetic**. Values are constructed to be
internally consistent and pedagogically useful. Nothing here is a real patient
record, and nothing here is clinical advice.

### Conventions
* Errors use an RFC-7807-flavoured body (`type`, `title`, `status`, `detail`).
* Every response carries `X-Request-ID`; quote it in bug reports.
* Case identifiers accept either the numeric id or the case code (`THY-001`).
"""


def configure_logging(settings: Settings) -> None:
    level = getattr(logging, settings.log_level, logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        fmt = "%(message)s" if settings.log_json else "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(handler)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        create_all()
        if settings.auto_seed:
            # Imported lazily: seeding pulls in the JSON corpus, which we do not
            # want to pay for in unit tests that stub the database.
            from .seed import seed_database

            report = seed_database(force=settings.reseed_on_boot)
            logger.info(
                "seed complete: %s cases, %s reference intervals (%s)",
                report.cases_loaded,
                report.intervals_loaded,
                "reseeded" if report.reseeded else "existing data kept",
            )
        logger.info(
            "%s v%s ready in %s mode (chaos=%s)",
            settings.app_name,
            settings.app_version,
            settings.environment,
            settings.chaos_enabled,
        )
        yield
        logger.info("shutting down")

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=API_DESCRIPTION,
        default_response_class=ORJSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        root_path=settings.root_path,
        lifespan=lifespan,
        contact={"name": "MedSimQA Platform Team", "email": "platform@medsimqa.invalid"},
        license_info={"name": "Apache-2.0"},
    )

    # --- middleware (outermost first) --------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-Total-Count",
            "X-Response-Time-Ms",
            "Server-Timing",
            "Location",
        ],
        max_age=600,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ChaosMiddleware, settings=settings)
    app.add_middleware(RequestContextMiddleware, settings=settings)

    # --- exception handlers ------------------------------------------------
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        body = ErrorDetail(
            type=f"https://medsimqa.dev/errors/{exc.status_code}",
            title=_title_for(exc.status_code),
            status=exc.status_code,
            detail=str(exc.detail),
            instance=str(request.url.path),
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "location": ".".join(str(part) for part in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        body = ErrorDetail(
            type="https://medsimqa.dev/errors/validation",
            title="Request validation failed",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{len(errors)} field(s) failed validation.",
            instance=str(request.url.path),
            errors=errors,
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=body.model_dump())

    @app.exception_handler(ConnectionResetError)
    async def reset_handler(request: Request, exc: ConnectionResetError):  # type: ignore[no-untyped-def]
        return await connection_reset_handler(request, exc)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error on %s", request.url.path)
        detail = repr(exc) if settings.debug else "An unexpected error occurred."
        body = ErrorDetail(
            type="https://medsimqa.dev/errors/internal",
            title="Internal server error",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            instance=str(request.url.path),
            request_id=getattr(request.state, "request_id", None),
        )
        return JSONResponse(status_code=500, content=body.model_dump())

    # --- routes ------------------------------------------------------------
    app.include_router(health.router)
    app.include_router(cases.router, prefix=settings.api_prefix)
    app.include_router(reference.router, prefix=settings.api_prefix)
    app.include_router(evaluation.router, prefix=settings.api_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "api": settings.api_prefix,
            "health": "/healthz",
        }

    return app


def _title_for(status_code: int) -> str:
    return {
        400: "Bad request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not found",
        405: "Method not allowed",
        409: "Conflict",
        413: "Payload too large",
        415: "Unsupported media type",
        422: "Unprocessable entity",
        429: "Too many requests",
        500: "Internal server error",
        502: "Bad gateway",
        503: "Service unavailable",
        504: "Gateway timeout",
    }.get(status_code, "Error")


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    _settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=_settings.host,
        port=_settings.port,
        reload=_settings.debug,
        log_level=_settings.log_level.lower(),
    )
