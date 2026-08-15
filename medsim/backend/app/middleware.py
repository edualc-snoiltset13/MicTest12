"""Cross-cutting HTTP middleware: request IDs, structured access logs, timing,
and the deliberately-hostile "chaos" layer used by the Phase 3 QA suite.

The chaos middleware is what lets the network-interception tests run in CI
without a real MITM proxy in the loop: the same failure modes a Charles/Proxyman
rewrite rule would produce (added latency, dropped connections, truncated or
malformed JSON) can be requested per-request with headers, or switched on
globally with environment variables. It is hard-disabled when
``environment == production``.
"""

from __future__ import annotations

import json
import logging
import random
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, PlainTextResponse

from .config import Settings

logger = logging.getLogger("medsim.access")

CallNext = Callable[[Request], Awaitable[Response]]

# Header names understood by the chaos layer. Kept in one place because the
# Cypress suite and the proxy fixtures both import this list (via the generated
# qa/proxy/chaos-headers.json).
CHAOS_HEADERS = {
    "latency": "X-Chaos-Latency-Ms",
    "status": "X-Chaos-Status",
    "malformed": "X-Chaos-Malformed",
    "truncate": "X-Chaos-Truncate",
    "drop": "X-Chaos-Drop",
    "content_type": "X-Chaos-Content-Type",
    "empty": "X-Chaos-Empty",
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign/propagate a request id and emit one structured log line per call."""

    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        header = self.settings.request_id_header
        request_id = request.headers.get(header) or uuid.uuid4().hex
        request.state.request_id = request_id

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            raise

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers[header] = request_id
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"
        # Server-Timing lets the Cypress performance assertions read backend
        # time straight out of the browser without a custom instrumentation hook.
        response.headers["Server-Timing"] = f"app;dur={duration_ms:.2f}"

        payload = {
            "event": "request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        if self.settings.log_json:
            logger.info(json.dumps(payload))
        else:
            logger.info(
                "%s %s -> %s (%.1f ms) rid=%s",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                request_id,
            )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Baseline hardening headers.

    The CSP is intentionally strict and does *not* allow inline script. The
    frontend is a compiled Vite bundle with no inline handlers, so this costs
    nothing; ``style-src 'unsafe-inline'`` remains because Tailwind's runtime
    utilities and the chart components set inline `style` for computed
    positions.
    """

    CSP = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self' http://localhost:8000 ws://localhost:5173; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        response.headers.setdefault("Content-Security-Policy", self.CSP)
        return response


class ChaosMiddleware(BaseHTTPMiddleware):
    """Fault injection for resilience testing.

    Per-request control (preferred in tests, because it is deterministic):

        curl -H 'X-Chaos-Latency-Ms: 4000' ...
        curl -H 'X-Chaos-Status: 503' ...
        curl -H 'X-Chaos-Malformed: 1' ...      # syntactically invalid JSON
        curl -H 'X-Chaos-Truncate: 40' ...      # first 40 bytes of the body only
        curl -H 'X-Chaos-Drop: 1' ...           # connection reset mid-flight
        curl -H 'X-Chaos-Content-Type: text/html' ...
        curl -H 'X-Chaos-Empty: 1' ...          # 200 with a zero-length body

    Global probabilistic control (soak/monkey runs) comes from
    ``MEDSIM_CHAOS_ERROR_RATE`` / ``MEDSIM_CHAOS_MALFORMED_RATE``.
    """

    def __init__(self, app, settings: Settings) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.settings = settings
        self._rng = random.Random(20260815)

    async def dispatch(self, request: Request, call_next: CallNext) -> Response:
        if not self.settings.chaos_enabled or self.settings.is_production:
            return await call_next(request)

        headers = request.headers

        # 1. Latency (header wins over the global floor).
        latency_ms = _int_header(headers, CHAOS_HEADERS["latency"], self.settings.chaos_latency_ms)
        if latency_ms > 0:
            import asyncio

            await asyncio.sleep(latency_ms / 1000.0)

        # 2. Hard connection drop. Raising here severs the response before any
        #    bytes are written, which the browser surfaces as ERR_EMPTY_RESPONSE
        #    / a fetch TypeError — the same shape as a proxy killing the socket.
        if _flag(headers, CHAOS_HEADERS["drop"]):
            raise ConnectionResetError("chaos: connection dropped before response")

        # 3. Forced status code.
        forced_status = _int_header(headers, CHAOS_HEADERS["status"], 0)
        if forced_status == 0 and self.settings.chaos_error_rate > 0:
            if self._rng.random() < self.settings.chaos_error_rate:
                forced_status = self._rng.choice([500, 502, 503, 504])
        if forced_status:
            return JSONResponse(
                status_code=forced_status,
                content={
                    "type": "https://medsimqa.dev/errors/chaos",
                    "title": "Injected fault",
                    "status": forced_status,
                    "detail": "Response synthesised by the chaos middleware.",
                    "request_id": getattr(request.state, "request_id", None),
                },
            )

        response = await call_next(request)

        # 4. Body corruption. Must buffer the streaming body first.
        wants_malformed = _flag(headers, CHAOS_HEADERS["malformed"]) or (
            self.settings.chaos_malformed_rate > 0
            and self._rng.random() < self.settings.chaos_malformed_rate
        )
        truncate_at = _int_header(headers, CHAOS_HEADERS["truncate"], 0)
        override_ct = headers.get(CHAOS_HEADERS["content_type"])
        wants_empty = _flag(headers, CHAOS_HEADERS["empty"])

        if not (wants_malformed or truncate_at or override_ct or wants_empty):
            return response

        body = b""
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            body += chunk if isinstance(chunk, bytes) else chunk.encode()

        if wants_empty:
            body = b""
        elif wants_malformed:
            # Deliberately unbalanced braces + a trailing comma: fails
            # JSON.parse at a *plausible* offset rather than on byte 0, which is
            # the realistic proxy-rewrite failure mode.
            body = body[: max(1, len(body) // 2)] + b',,{"truncated": true'
        elif truncate_at:
            body = body[:truncate_at]

        new_headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in {"content-length", "content-type"}
        }
        media_type = override_ct or response.media_type or "application/json"
        return Response(
            content=body,
            status_code=response.status_code,
            headers=new_headers,
            media_type=media_type,
        )


def _int_header(headers, name: str, default: int) -> int:  # type: ignore[no-untyped-def]
    raw = headers.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(0, min(value, 60_000))


def _flag(headers, name: str) -> bool:  # type: ignore[no-untyped-def]
    raw = headers.get(name)
    return bool(raw) and raw.lower() not in {"0", "false", "no", ""}


async def connection_reset_handler(_request: Request, _exc: Exception) -> Response:
    """Turn the chaos drop into a bare 502 with no JSON body, mimicking a proxy
    that killed the upstream connection."""
    return PlainTextResponse("", status_code=502)
