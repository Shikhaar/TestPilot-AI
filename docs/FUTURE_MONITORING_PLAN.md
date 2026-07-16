# 📊 Future Roadmap: Observability & Monitoring Redesign

This document outlines the proposed architecture and implementation plan for a production-grade, native observability dashboard for TestPilot AI. 

The goal is to replace direct user exposure of Celery Flower and Grafana with a premium, unified engineering platform dashboard built directly into the Next.js application, consuming a custom FastAPI metrics aggregation layer.

---

## 🏗️ Proposed Architecture

```
                               ┌───────────────────────────┐
                               │   Next.js Monitoring UI   │
                               │   (Native, Dark Theme)    │
                               └─────────────▲─────────────┘
                                             │
                                             │ REST API (/api/v1/dashboard/*)
                                             │
                               ┌─────────────┴─────────────┐
                               │  FastAPI Metrics Service  │
                               │  (Aggregates Prom Metrics)│
                               └─────────────▲─────────────┘
                                             │
                                             │ Scraping / Querying
                                             │
                               ┌─────────────┴─────────────┐
                               │        Prometheus         │
                               └─────────────▲─────────────┘
                                             │
      ┌───────────────────────┬──────────────┼──────────────┬───────────────────────┐
      │                       │              │              │                       │
┌─────┴─────┐           ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐           ┌─────┴─────┐
│  FastAPI  │           │  Celery   │  │   Redis   │  │ Postgres  │           │  Qdrant   │
│ (Backend) │           │ (Workers) │  │  (Cache)  │  │ (RDBMS)   │           │ (Vectors) │
└───────────┘           └───────────┘  └───────────┘  └───────────┘           └───────────┘
```

> [!IMPORTANT]
> **Access Security Principle:** Prometheus, Grafana, and Flower remain active in the background for internal system development and debugging, but must **never** be exposed to end-users or embedded directly in the frontend via iframes.

---

## 📈 Components to Instrument & Collect

### 1. Backend (FastAPI)
* Request count & response statuses
* API endpoint latency profiles
* Authentication failures
* LLM endpoint call times
* Webhook event arrival counters

### 2. Celery Worker Queue
* Active worker counts
* Queue length & depth per topic
* Executing, succeeded, failed, and retried task counts
* Average execution time per job type
* Stalled or long-running task alerts

### 3. Redis Broker
* In-memory usage
* Queue depth
* Operations/sec rate

### 4. PostgreSQL
* Active connections
* Latency & query execution times
* Slow-query flags

### 5. Qdrant Vector DB
* Search latency
* Vector insertion speed
* Collection size metrics

### 6. LLM Integration (OpenAI/LiteLLM)
* Total requests
* Token consumption metrics (Input vs. Output tokens)
* Provider distribution (OpenAI, Gemini, etc.)
* Cumulative API cost tracking
* Rate-limit hits and failed/retried LLM attempts

### 7. Codebase Processing
* **Indexing:** Files processed, embeddings created, average ingestion durations.
* **PR Analysis:** Diff parsing speed, risk calculation durations, ast-mapping duration.
* **Testing:** Pytest suites compiled, pass/fail rates, testing coverage metrics, individual test execution runtime.

---

## 🔌 FastAPI Metrics Service (`backend/app/monitoring/`)

Create endpoints that query the Prometheus API, parse results, and format it into clean JSON responses for the UI:

* `GET /dashboard/overview`: High-level system vitals, daily token consumption, active queue depth, service status lights.
* `GET /dashboard/workers`: Worker statuses, active jobs, completed jobs, and processing telemetry.
* `GET /dashboard/performance`: Latency analysis for APIs, indexing pipeline, LLM calls, and testing subprocesses.
* `GET /dashboard/ai`: Token usage, token pricing breakdown, and LLM providers distribution.
* `GET /dashboard/queue`: Running jobs, pending queue capacity, and retry schedules.
* `GET /dashboard/tests`: Generation counts, pass rates, test durations, and failures breakdown.
* `GET /dashboard/repositories`: Ingested file size, vector sizes, indexing progress.
* `GET /dashboard/pr`: Pull Request risk indicators, analysis execution durations.
* `GET /dashboard/system`: Low-level system resources (CPU, Memory, PostgreSQL, Redis, Qdrant).
* `GET /dashboard/activity`: Event timeline feed.

---

## 🎨 Next.js Dashboard Layout & UI Design

The UI will be designed natively inside the Next.js App Router using the existing Tailwind styling system, combined with modern elements inspired by Linear, Datadog, and Vercel.

### Key Sections:
1. **Overview**: Status indicators for all platform subsystems, metrics summary cards (Cost today, active queues, average risk scores).
2. **System Vitals**: Memory/CPU health of the cluster, DB pool usage.
3. **Workers**: Dynamic table listing all active workers, workloads, and runtime timelines.
4. **Queue**: Inflow/outflow history charts, pending tasks queue metrics.
5. **AI Usage**: Graphs for daily costs, input/output tokens, and model distribution.
6. **Repositories**: Dashboard detailing file indexes, vector count, and last indexed run status.
7. **Pull Requests**: Visual timeline logs tracking webhook ingestion, repository checkout, dependency resolution, test generation, execution, and pull request posting.
8. **Performance**: Aggregated bar/line graphs showing response time distribution for various app modules.
9. **Tests**: Pytest generation success metrics, execution reports, test runner durations.
10. **Activity Feed**: Interactive timeline log tracking historical pipeline transactions (e.g., *14:15 - Generated 12 tests*, *14:17 - Review Posted*).
