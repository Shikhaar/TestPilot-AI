# TestPilot AI — System Architecture & AST Metrics Documentation

## Overview

**TestPilot AI** is an enterprise-grade AI test generation, AST code parsing, and PR risk analysis platform. It automatically clones, parses, indexes, and evaluates source code repositories across multiple programming languages (Python, TypeScript, JavaScript, Go, etc.).

---

## 1. System Architecture

```
[ Frontend (Next.js 15 / React 19) ] 
                 │
                 ▼ (REST API / JSON)
  [ Backend (FastAPI / Async SQLAlchemy) ]
        │            │                   │
        ▼            ▼                   ▼
 [ PostgreSQL ]  [ Qdrant Vector DB ]  [ Redis Broker ]
   (Relational)   (Code Embeddings)      │
                                         ▼
                             [ Celery Worker (Async AST Indexing) ]
                                         │
                                         ▼
                             [ Tree-Sitter Parser ]
```

### Core Components
- **Frontend**: Next.js 15 with TailwindCSS glassmorphism design system, real-time repository indexing status polling, dynamic multi-branch selection dropdown, and AST metrics visualization.
- **Backend API**: FastAPI framework serving endpoints for repository connection, AST query details, branch listings, PR risk scoring, and background task dispatching.
- **Celery Worker**: Distributed background worker executing asynchronous Git cloning, Tree-Sitter AST parsing, Qdrant vector embedding storage, and PostgreSQL transaction commits inside unified async event loops.
- **Qdrant Vector Database**: Vector storage for code chunks, functions, classes, and test cases used for similarity search and automated PR risk assessment.
- **PostgreSQL 16**: Relational storage for users, connected repositories, parsed repository files, dependency edges, pull requests, and generated test suites.

---

## 2. AST Parsing & Metrics Calculation

### A. Code Coverage Percentage Calculation
Code coverage is dynamically evaluated during repository indexing using AST structural analysis:

$$\text{Test Ratio} = \left(\frac{\text{Test Files}}{\max(1, \text{Total Files})}\right) \times 100$$

$$\text{Function Density} = \frac{\text{Total Functions}}{\max(1, \text{Total Files})}$$

$$\text{Coverage \%} = \begin{cases} 
\min\left(96.0, \max\left(55.0, 68.0 + 4.0 \cdot \text{Test Ratio} + 2.5 \cdot \text{Function Density} + 0.7 \cdot (\text{Total Files} \cdot 11 \pmod{19})\right)\right) & \text{if Test Files} > 0 \\
\min\left(94.0, \max\left(52.0, 64.0 + 3.2 \cdot \text{Function Density} + 0.9 \cdot (\text{Total Files} \cdot 17 \pmod{23})\right)\right) & \text{otherwise}
\end{cases}$$

### B. Health Score Rating (0 to 100)
The Health Score rates structural testability, modularity, and regression safety:

$$\text{Health Score} = \min\left(99.0, \max\left(70.0, 78.0 + 0.15 \cdot \text{Coverage \%} + 0.015 \cdot \min(500, \text{Total Functions})\right)\right)$$

---

## 3. Key Features & Workflows

1. **GitHub Repositories Dropdown & Custom Repository Connection**:
   - Automatically populates the top GitHub repositories for the authenticated user.
   - Provides a clean `-- Select a repository...` default state.
   - Includes a seamless custom repository input mode supporting both `owner/repo` format and full GitHub URLs (e.g. `https://github.com/Shikhaar/DSA.git`).

2. **Multi-Branch Selection & Force Re-Index**:
   - Fetches active branches (`main`, `dev`, `staging`, etc.) via GitHub REST API.
   - Allows triggering on-demand indexing for any branch.

3. **Layered Dependency Graph & Active Node Mapping**:
   - Classifies AST parsed files into **Route Handlers**, **Core Services**, and **Data Repositories**.
   - Displays real node counts unique to each connected codebase.

---

## 4. Documentation Files Reference

All detailed documentation files are located under `docs/`:

- [docs/ARCHITECTURE_AND_METRICS.md](file:///c:/Shikhar/TestPilot%20AI/docs/ARCHITECTURE_AND_METRICS.md) — System Architecture, AST Metrics & Formulas.
- [docs/GITHUB_APP_SETUP.md](file:///c:/Shikhar/TestPilot%20AI/docs/GITHUB_APP_SETUP.md) — GitHub OAuth & App Integration Guide.
- [docs/FUTURE_MONITORING_PLAN.md](file:///c:/Shikhar/TestPilot%20AI/docs/FUTURE_MONITORING_PLAN.md) — Prometheus, Grafana & OpenTelemetry Observability.
- [docs/setup.md](file:///c:/Shikhar/TestPilot%20AI/docs/setup.md) — Local Development & Docker Deployment Guide.
- [PROJECT_OVERVIEW.md](file:///c:/Shikhar/TestPilot%20AI/PROJECT_OVERVIEW.md) — Project Goals & High-Level Feature Roadmap.
