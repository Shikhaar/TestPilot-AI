# Future Implementation Plan - Autonomous Regression Intelligence Platform

Transforming **TestPilot AI** from a linear test generator into an **Autonomous Regression Intelligence Platform** driven by closed-loop reasoning, dedicated repair agents, deterministic risk/confidence scoring, semantic repository memory, and full-pipeline MCP tools.

---

## Task Roadmap

```
Task 1: Self-Healing Pipeline + Dedicated Patch Agent + Modular AgentState
 │
 ▼
Task 2: Repository Memory (Regression Memory + Hybrid RAG)
 │
 ▼
Task 3: Deterministic Risk & Mathematical Confidence Scoring Engine
 │
 ▼
Task 4: Commercial-Grade GitHub PR Bot
 │
 ▼
Task 5: Full Reasoning Pipeline MCP Server
```

---

## Detailed Task Breakdown

### Task 1: Self-Healing Test Generation Loop & Metrics Telemetry

#### 1. Modular State Composition
Split the monolithic state in `app/agents/state.py` into clean TypedDict sub-states:
- `WorkflowState`: `pr_id`, `repository_id`, `head_sha`, `current_agent`, `completed_agents`, `errors`
- `DiffState`: `changed_files`, `changed_nodes`, `dependency_graph_edges`
- `TestPlanState`: `test_plan` (`target_functions`, `required_test_types`, `mock_requirements`)
- `GenerationState`: `generated_tests`
- `ExecutionState`: `execution_results`, `failure_analyses`
- `RepairState`: `repair_attempt`, `max_repair_attempts`, `repaired_tests`, `patch_history`
- `MetricsState`: `iteration_telemetry` (`attempt`, `total`, `passed`, `failed`, `pass_rate`)
- `AgentState`: Inherits/composes all sub-states cleanly.

#### 2. Dedicated Repair Agent & Strategy Planner
- **Test Strategy Planner (`planner_agent.py`)**: Analyzes git diffs and emits a structured `TestPlan` dict defining test types required (boundary, negative, async mock) per changed node.
- **Dedicated Repair Agent (`test_patch_agent.py`)**: Accepts failed tests, error tracebacks, and `FailureAnalysis` output, and generates precise code patches for existing test files (fixing imports, mock signatures, or assertion logic) without re-generating unchanged tests from scratch.

#### 3. Closed-Loop LangGraph Pipeline (`graph.py`)
- Register `test_patch_agent` node.
- Flow: `planner` $\rightarrow$ `diff` $\rightarrow$ `dependency` $\rightarrow$ `impact` $\rightarrow$ `search` $\rightarrow$ `test_discovery` $\rightarrow$ `test_generator` $\rightarrow$ `execution` $\rightarrow$ `failure_analysis` $\rightarrow$ **`test_patch_agent`** $\rightarrow$ **`execution`** (Loop) $\rightarrow$ `review` $\rightarrow$ `END`.
- Conditional edge `should_continue_self_healing`:
 - If `failed > 0` and `repair_attempt < max_repair_attempts`: route to `test_patch_agent`.
 - Else: route to `review_agent`.

#### 4. Metrics Recording (`execution_agent.py`)
- Record iteration progression in `iteration_telemetry` (e.g., `Iteration 1: 63%` $\rightarrow$ `Iteration 2: 100%`).

---

### Task 2: Repository Memory (Regression Memory & Hybrid RAG)
- Parse and index test fixtures (`conftest.py`, `jest.setup.js`) and mock helpers.
- Implement **Regression Memory**: Automatically embed and store passing AI-generated tests into vector storage (Qdrant/ChromaDB) mapped to:
 $$\text{PR} \rightarrow \text{Changed Function} \rightarrow \text{Generated Test} \rightarrow \text{Execution Result} \rightarrow \text{Repaired Version}$$
- Implement Hybrid Retrieval: Combine semantic search over embeddings with BM25 sparse keyword search to retrieve matching test patterns for similar functions.

---

### Task 3: Deterministic Risk & Mathematical Confidence Scoring Engine
- Compute per-test **Confidence Scores** ($0.0 - 1.0$) using a mathematical formula based on measurable signals:
 $$\text{Confidence} = 0.25 \cdot \text{Execution Success} + 0.25 \cdot \text{Retrieval Similarity} + 0.20 \cdot \text{AST Coverage} + 0.15 \cdot \text{Dependency Coverage} + 0.15 \cdot \text{Complexity Score}$$
- Compute **PR Risk Score** based on AST dependency graph centrality, code complexity, code churn, missing test coverage, and critical services touched (Auth, Payment, caching).
- Let the LLM generate natural language explanations of the score, but keep scoring calculation deterministic.

---

### Task 4: Commercial-Grade GitHub PR Bot
- Extend `github_service.py` to post highly structured, interactive PR reviews:
 * Regression Risk Level & Score
 * Mathematical Confidence Metrics
 * Breakdown of Critical Paths (e.g. Authentication, Payments)
 * Missing Coverage Alerts
 * Option to commit passing generated tests directly to the PR branch.

---

### Task 5: Model Context Protocol (MCP) Server Integration
- Create an MCP server (`app/mcp/server.py`) exposing the full reasoning pipeline to IDEs (Cursor, VS Code, Antigravity) via tools:
 * `testpilot.analyze_pr(pr_id)`
 * `testpilot.predict_risk(pr_id)`
 * `testpilot.generate_tests(file_path)`
 * `testpilot.heal_tests(file_path)`
 * `testpilot.get_metrics()`
 * `testpilot.show_dependency_graph()`
