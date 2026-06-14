import logging
import time
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("lingualeap")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed", extra={"request_id": request_id, "path": request.url.path})
            raise
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        response.headers["x-request-id"] = request_id
        response.headers["x-response-time-ms"] = str(elapsed_ms)
        logger.info(
            "request_complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": elapsed_ms,
            },
        )
        return response


def security_headers(response):
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-frame-options"] = "DENY"
    response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
    response.headers["permissions-policy"] = "camera=(), geolocation=(), microphone=(self)"
    response.headers["content-security-policy"] = (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    return response
