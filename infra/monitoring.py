from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response

from core.config import get_settings

try:  # Optional Sentry support
    import sentry_sdk
except ImportError:  # pragma: no cover
    sentry_sdk = None

REQUEST_LATENCY = Histogram(
    "realtor_request_latency_seconds", "Latency of API requests", buckets=(0.1, 0.3, 1.0, 3, 10)
)
REQUEST_COUNT = Counter(
    "realtor_request_count", "Total API requests", labelnames=("method", "endpoint", "status")
)
ACTIVE_TASKS = Gauge("realtor_active_tasks", "Background tasks currently running")


def register_instrumentation(app: FastAPI) -> None:
    settings = get_settings()

    if settings.sentry_dsn and sentry_sdk is not None:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)

    @app.middleware("http")
    async def metrics_middleware(request, call_next):  # type: ignore[override]
        if not settings.prometheus_enabled:
            return await call_next(request)
        method = request.method
        path = request.url.path
        with REQUEST_LATENCY.time():
            response = await call_next(request)
        REQUEST_COUNT.labels(method, path, response.status_code).inc()
        return response

    @app.get("/metrics")
    def metrics():  # pragma: no cover - simple passthrough
        if not settings.prometheus_enabled:
            raise RuntimeError("Prometheus disabled")
        return Response(content=generate_latest(), media_type="text/plain")
