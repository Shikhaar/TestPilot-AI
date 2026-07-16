# TestPilot AI — Phase 4 & 5 Refined Implementation Plan (V2)

This plan integrates the user's recommendations for a production-grade SaaS experience, focusing on professional security (HTTP-only secure cookie refresh tokens), scalable API layouts, developer-centric metrics, layered dependency graphs, interactive test committing workflows, and a real-time PR Timeline.

---

## User Review Required

> [!IMPORTANT]
> **HTTP-Only Secure Cookie Flow**:
> 1. GitHub OAuth callback exchanges code at `POST /api/v1/auth/github/callback`.
> 2. Backend returns short-lived JWT Access Token in JSON response body.
> 3. Backend sets the long-lived Refresh Token in a `Set-Cookie` header (`HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth/refresh`).
> 4. Next.js dashboard interceptor intercepts `401 Unauthorized` and hits `POST /api/v1/auth/refresh` (which automatically forwards the cookie) to get a new Access Token.
> **Dependency Graph Layering**:
> * Instead of individual files, React Flow will render grouped cluster nodes representing codebase architectural layers: **Controllers/Routes** ➔ **Services/Agents** ➔ **Repositories/Models** ➔ **Databases/External API Calls**.

---

## Proposed Changes

### 1. Backend Authentication Update
* Modify `app/api/v1/auth.py` to set the refresh token as a cookie and return only the access token in the JSON body.
* Update `app/core/security.py` to handle secure cookie serialization and domain parity configuration.

### 2. Frontend Client Layout (`frontend/src/lib/api/`)
* **`client.ts`**: Axios instance with automatic response interceptor detecting expired access tokens and calling `/auth/refresh` using cookie credentials.
* **`auth.ts`**, **`repositories.ts`**, **`pullRequests.ts`**, **`dashboard.ts`**, **`tests.ts`**, **`ai.ts`**: Modular API fetch hooks.

### 3. Dashboard Page (`frontend/src/app/page.tsx`)
* Developer-focused dashboard cards showing:
  * Repositories connected & indexed.
  * Pull Requests awaiting review.
  * Total AI-generated test count.
  * Average risk score.
  * Codebase coverage percentage.
  * Current AI cost in USD.
  * Celery task queue length & worker processing success rate.

### 4. Repository Detail Page (`frontend/src/app/repositories/[id]/page.tsx`)
* Insights-style overview showcasing:
  * Architecture summary (layered structure mapping).
  * Grouped dependency graph nodes.
  * Language distribution ratios & test framework detections.
  * Repository health scores.
  * List of recent PR reviews and test run histories.

### 5. Pull Request Page (`frontend/src/app/pull-requests/[id]/page.tsx`)
* Tab-oriented view structure:
  1. **Overview**: Displaying PR details, commit lists, and the **PR Timeline** ( webhook received ➔ cloned ➔ graph built ➔ generated tests ➔ test results ➔ review posted).
  2. **Review**: Markdown code review draft with actions to post or update the GitHub check runs.
  3. **Dependency Graph**: Layered node flow (Controller ➔ Service ➔ Repository ➔ DB).
  4. **Generated Tests**: Side-by-side Monaco comparison editor with a workflow bar (`[Accept] [Edit] [Copy] [Commit to Branch] [Open PR]`).
  5. **Failures**: Test failures showing tracebacks alongside AI-generated fix recommendations.
  6. **Logs & Coverage**: Complete execution logs and coverage delta charts.

### 6. Monitoring & Metrics (`backend/app/main.py`)
* Collect and expose to Prometheus:
  * API endpoints latency.
  * Celery queue wait times.
  * Embedding chunk computation speeds.
  * LiteLLM response durations.
  * Agent run execution step durations, retries, and errors.
* Pre-configured Grafana JSON layout at `infra/grafana/dashboards/testpilot.json` mapping:
  * Repository indexing duration histograms.
  * PR analysis times.
  * Active Celery worker throughput and Redis queue depths.

---

## Verification Plan

### Automated Build Verify
```bash
# Verify Next.js build
cd frontend && npm run build
```

### Manual Visual Checks
1. Initiate GitHub Login -> Confirm HTTP-only cookie is set under browser application tab.
2. Trigger PR review -> Watch WebSocket stream populate the PR Timeline step-by-step.
3. Open Dependency Graph -> Verify that nodes are clustered by layer rather than displaying unreadable file lists.
