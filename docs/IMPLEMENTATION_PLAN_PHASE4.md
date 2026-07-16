# TestPilot AI — Phase 4 Implementation Plan

This plan details the design, structure, and execution steps for **Phase 4: Next.js Frontend Dashboard, Visualizations, and Monitoring**.

---

## User Review Required

> [!IMPORTANT]
> **Authentication Method**: Next.js will connect to FastAPI JWT authentication. I plan to store the JWT token in `localStorage` and pass it in the `Authorization: Bearer <token>` headers for queries. Let me know if you prefer HTTP-only secure cookies (requires backend domain parity setup).
> **UI Components**: I will use a dark, premium glassmorphism theme using Tailwind CSS and Lucide React icons.
> **Grafana Dashboards**: Grafana will connect to the Prometheus instance. I will create a pre-configured dashboard JSON file in the infrastructure config directory.

---

## Open Questions

> [!IMPORTANT]
> 1. **React Flow version**: I will use the standard `@xyflow/react` library for displaying the module dependency graph. Do you have any specific graph layouts or styling preferences?
> 2. **WebSocket connection**: The WebSocket connection is established at `ws://localhost:8000/ws/pr/{pr_id}`. I will use React state context to hook WebSocket progress messages into the PR detail component.

---

## Proposed Changes

### Next.js Frontend: `frontend/`

#### [NEW] [api.ts](file:///c:/Shikhar/TestPilot%20AI/frontend/src/lib/api.ts)
* Create HTTP request client using Fetch API wrapper supporting Authorization headers, automatic refresh tokens, and basic REST wrappers for endpoints:
  * `/auth/github/login`
  * `/auth/github/callback`
  * `/repositories`
  * `/pr`
  * `/tests`
  * `/ai/chat`
  * `/ai/search`
  * `/dashboard`

#### [NEW] [layout.tsx](file:///c:/Shikhar/TestPilot%20AI/frontend/src/app/layout.tsx)
* Setup base glassmorphism layout, fonts (Inter), toast alerts provider, and global dashboard headers/sidebars.

#### [NEW] [page.tsx](file:///c:/Shikhar/TestPilot%20AI/frontend/src/app/page.tsx)
* Implement Dashboard Overview panel:
  * Connection stats (total repositories, indexed file counts).
  * Recent Pull Requests table showing analysis status, risk scores, and commit details.
  * AI token usage graphs and cost meters.

#### [NEW] [repositories/[id]/page.tsx](file:///c:/Shikhar/TestPilot%20AI/frontend/src/app/repositories/[id]/page.tsx)
* Implement Repository Detail panel:
  * File list, health metrics, test framework type.
  * Indexing status progress bar connected to the Repository WebSocket.

#### [NEW] [pull-requests/[id]/page.tsx](file:///c:/Shikhar/TestPilot%20AI/frontend/src/app/pull-requests/[id]/page.tsx)
* Implement Pull Request Analysis panel:
  * WebSocket-connected terminal displaying real-time agent pipeline logs.
  * Risk evaluation metrics (risk score dial, list of warning factors).
  * Review Comment text area showcasing the synthesized Markdown draft with an action button to "Post to GitHub".
  * Tabbed views showing:
    * **Dependency Graph** (React Flow diagram).
    * **Generated Tests** (Side-by-side Monaco diff-editor display).
    * **Test Execution Results** (Failing tests and Failure Analysis fix recommendations).

#### [NEW] [dependency-graph.tsx](file:///c:/Shikhar/TestPilot%20AI/frontend/src/components/dependency-graph.tsx)
* Create React Flow visualizer rendering nodes (file pathways) and edges (imports) with interactive hover actions highlighting blast-radius downstream items.

---

### Infrastructure: `infra/`

#### [NEW] [testpilot.json](file:///c:/Shikhar/TestPilot%20AI/infra/grafana/dashboards/testpilot.json)
* Pre-configured Grafana dashboard template mapping:
  * HTTP request counts and latency distributions.
  * Celery worker active tasks, queue backlogs, and execution success rates.
  * LangGraph agent run frequencies and token/cost tracking histograms.

---

## Verification Plan

### Automated Tests
* Validate Next.js compile build and check for type warnings:
  ```bash
  cd frontend
  npm run build
  ```

### Manual Verification
1. Run local development container system (`make dev`).
2. Log in via GitHub OAuth -> Verify authentication redirect flows.
3. Access repository lists, index a mock repository, and observe progress animations.
4. Trigger PR analysis -> Observe real-time WebSocket progress alerts in the analysis panel.
5. Review the resulting graph structure, Monaco code editor displays, and Grafana panel charts.
