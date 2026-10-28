"""Demo API - app de ejemplo para aprender Observabilidad.

Expone:
  - /metrics      -> métricas en formato Prometheus (pull)
  - endpoints     -> tráfico real del negocio (items, search, checkout)
  - trazas OTel   -> enviadas al OpenTelemetry Collector por OTLP (push)

Falla de forma inyectable para poder jugar con SLIs y SLOs.
"""

import logging
import os
import random
import re
import time

from fastapi import FastAPI, HTTPException, Request, Response
from opentelemetry import trace
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

# ---------------------------------------------------------------------------
# Logging estructurado (key=value) -> lo lee Promtail y lo manda a Loki.
# Escribimos a stdout (para `docker logs`) y a un archivo compartido
# con Promtail dentro del volumen `app_logs`.
# ---------------------------------------------------------------------------
LOG_DIR = "/var/log/app"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("demo-api")
logger.setLevel(logging.INFO)

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
handler_stdout = logging.StreamHandler()
handler_stdout.setFormatter(logging.Formatter(LOG_FORMAT))
handler_file = logging.FileHandler(os.path.join(LOG_DIR, "app.log"))
handler_file.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler_stdout)
logger.addHandler(handler_file)

# ---------------------------------------------------------------------------
# Métricas (client library oficial de Prometheus para Python)
# ---------------------------------------------------------------------------
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total de requests HTTP por método, ruta y código de status",
    ["method", "path", "status"],
)

HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "Latencia de requests HTTP en segundos",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

BUSINESS_TRANSACTIONS = Counter(
    "business_transactions_total",
    "Transacciones de negocio por resultado (success/failure)",
    ["transaction", "outcome"],
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Demo API", version="1.0.0")


def _normalize_path(path: str) -> str:
    """Baja la cardinalidad: /api/items/12345 -> /api/items/:id.
    Sin esto, cada id distinto crearía una serie nueva en Prometheus."""
    return re.sub(r"/\d+", "/:id", path)


def _maybe_fail(rate: float, dependency: str, transaction: str | None = None) -> None:
    """Inyecta fallos con probabilidad `rate`. Falla hacia HTTP 500."""
    if random.random() < rate:
        if transaction:
            BUSINESS_TRANSACTIONS.labels(transaction, "failure").inc()
        span = trace.get_current_span()
        span.set_attribute("error.dependency", dependency)
        raise HTTPException(status_code=500, detail=f"{dependency} unavailable")


@app.middleware("http")
async def observe_and_log(request: Request, call_next):
    """Middleware: mide y registra TODA request que entra a la app."""
    if request.url.path == "/metrics":
        return await call_next(request)

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("unhandled_exception=true")
        response = Response(status_code=500, content="Internal Server Error")

    duration_ms = (time.perf_counter() - start) * 1000
    path = _normalize_path(request.url.path)

    HTTP_DURATION.labels(request.method, path).observe(duration_ms / 1000)
    HTTP_REQUESTS.labels(request.method, path, response.status_code).inc()

    logger.info(
        f"method={request.method} path={path} status={response.status_code} "
        f"duration_ms={duration_ms:.1f}"
    )
    return response


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "demo-api", "docs": "/docs"}


# ----------------------------- Endpoints -------------------------------

@app.get("/api/items")
def list_items():
    _maybe_fail(float(os.environ.get("FAIL_RATE_ITEMS", "0.02")), "inventory_db")
    time.sleep(random.uniform(0.002, 0.03))
    n = random.randint(1, 8)
    return {"items": [{"id": i, "name": f"item-{i}"} for i in range(n)]}


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    _maybe_fail(float(os.environ.get("FAIL_RATE_ITEMS", "0.02")), "item_db")
    time.sleep(random.uniform(0.001, 0.01))
    return {"id": item_id, "name": f"item-{item_id}", "price": round(random.uniform(1, 100), 2)}


@app.get("/api/search")
def search(q: str = ""):
    _maybe_fail(float(os.environ.get("FAIL_RATE_SEARCH", "0.04")), "search_index", "search")
    time.sleep(random.uniform(0.01, 0.2))  # algunas búsquedas lentas
    n = random.randint(0, 30)
    BUSINESS_TRANSACTIONS.labels("search", "success").inc()
    return {"results": n, "items": [{"id": i} for i in range(n)]}


@app.post("/api/checkout")
def checkout():
    _maybe_fail(float(os.environ.get("FAIL_RATE_CHECKOUT", "0.08")), "payment_gateway", "checkout")
    time.sleep(random.uniform(0.1, 0.9))  # checkout es lento a propósito
    BUSINESS_TRANSACTIONS.labels("checkout", "success").inc()
    return {"order_id": random.randint(10000, 99999), "status": "confirmed"}
