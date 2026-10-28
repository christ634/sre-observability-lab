"""Generador de tráfico sintético.

Simula usuarios golpeando la API con un mix de rutas parecido al real:
más GETs de items, menos checkouts, etc. RPS configurable por env.
"""

import os
import random
import time

import requests

BASE = os.environ.get("APP_URL", "http://app:8000")
RPS = float(os.environ.get("RPS", "20"))

# (ruta, método, peso relativo)
ROUTES = [
    ("/api/items", "GET", 0.55),
    ("/api/items/1", "GET", 0.10),
    ("/api/search", "GET", 0.20),
    ("/api/checkout", "POST", 0.15),
]

paths = [r[0] for r in ROUTES]
weights = [r[2] for r in ROUTES]
methods = {r[0]: r[1] for r in ROUTES}

interval = 1.0 / RPS
print(f"loadgen iniciando: {BASE} @ {RPS:.0f} RPS", flush=True)

while True:
    t0 = time.perf_counter()
    path = random.choices(paths, weights=weights, k=1)[0]
    try:
        if methods[path] == "POST":
            requests.post(BASE + path, json={"items": [1, 2, 3]}, timeout=5)
        else:
            requests.get(BASE + path, timeout=5)
    except Exception as exc:
        print(f"request fallida: {type(exc).__name__}: {exc}", flush=True)
    time.sleep(max(0.0, interval - (time.perf_counter() - t0)))
