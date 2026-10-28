# SRE Observability Lab

A production-like observability stack built with OpenTelemetry, Prometheus, Loki, Tempo, and Grafana. This lab demonstrates SLI/SLO tracking, error budget burn-rate alerts, distributed tracing, centralized logging, and synthetic traffic generation.

## Architecture

```text
[LoadGen] -> [Demo API (FastAPI)] --(OTLP/gRPC)--> [OTel Collector]
                |                                       |-> [Tempo] (traces)
                |                                       |-> [Prometheus] (metrics + SLO rules)
                v
              [Logs] -> [Promtail] -> [Loki]
                                      ^
                                      |
                                    [Grafana] (dashboards + alerts)
```

## Stack

- **Application**: FastAPI (instrumented with OpenTelemetry)
- **Traces**: OpenTelemetry Collector → Tempo
- **Metrics**: Prometheus with custom SLI/SLO recording rules
- **Logs**: Promtail → Loki
- **Visualization/Alerts**: Grafana (provisioned dashboards & alert rules)
- **Traffic**: Load generator for realistic testing
- **Orchestration**: Docker Compose

## SRE Concepts Implemented

- **SLI/SLO**: Availability SLO of 99.5% (error budget = 0.5%)
- **Error Budget Burn Rate**: Multi-window, multi-burn-rate alerts based on the [Google SRE Workbook](https://sre.google/workbook/alerting-on-slos/)
- **Recording Rules**: Pre-computed SLIs over 5m/1h/6h/30d windows
- **Alerting**: Critical (14.4x burn in 1h) and Warning (2x burn in 6h)
- **Distributed Tracing**: End-to-end trace visibility with Tempo
- **Centralized Logging**: Structured logs correlated with traces/metrics

## Quick Start

```bash
# Start the full stack
docker compose up -d --build

# Access services
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Tempo: http://localhost:3200
# Loki: http://localhost:3100
```

## What I Practiced

- Building a full LGTM-style observability stack from scratch
- Writing Prometheus recording/alerting rules for SLOs
- Implementing multi-window burn-rate alerting
- OpenTelemetry instrumentation and collector pipelines
- Log aggregation with Loki/Promtail
- Grafana provisioning (datasources, dashboards, alerts as code)
- SRE reliability thinking with error budgets

## Author

[Christopher Cardozo](https://github.com/christ634) | Tech Support L1 turned SRE-focused engineer
