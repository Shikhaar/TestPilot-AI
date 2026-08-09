# TestPilot AI — Version 2.0.0 Implementation Plan

TestPilot AI Version 2 (v2.0.0) expands the platform into an enterprise-grade, multi-tenant AI software engineering suite featuring native monorepo graph resolution, real-time webhooks across all VCS providers, sandboxed containerized test execution, and automated pull request auto-remediation.

---

## Technical Goals & Architecture Milestones

### Phase 1: Native Monorepo Support & Enterprise Webhooks
- Multi-Package AST Graph Resolution: Extend Tree-sitter dependency parsing to support monorepos containing multiple independent service directories (npm workspaces, Lerna, Nx, Cargo workspaces, Go modules).
- Unified Webhook Receiver: Expand webhook endpoints (`/api/v1/webhooks/*`) to process pull request events, commit pushes, and comment triggers from Bitbucket, GitLab, and Azure DevOps in addition to GitHub.
- Scope-Based Indexing: Allow selective AST vector indexing for sub-directories and individual microservices within large repositories.

### Phase 2: Docker Containerized Test Sandbox & Isolation
- Host Subprocess to Docker Sandbox Migration: Transition test execution in `execution_agent_node` (`backend/app/agents/execution_agent.py`) from local host `subprocess.run()` calls to isolated ephemeral Docker sandbox containers (`docker run --rm --network none --memory=2g`).
- Sandbox Security Policy Enforcement: Enforce memory limits, CPU quotas, filesystem read-only locks, network isolation, and execution timeouts to protect host infrastructure from malicious or runaway test code.
- Multi-Language Runtime Images: Add pre-built runner images for Python (pytest), Node.js (jest/vitest), Go (`go test`), Java (`mvn test`), and Rust (`cargo test`).

### Phase 3: Automated Pull Request Auto-Remediation & Inline Annotations
- Manual Commit Button to Autonomous Remediation: Upgrade from manual UI test commitment (`POST /repositories/{id}/commit-tests`) to autonomous AI agent patch commits on target branches (`testpilot/fix-<pr-id>`).
- Inline Line-Level PR Annotations: Transition top-level PR summary comments into line-by-line inline code annotations on GitHub, Bitbucket, GitLab, and Azure DevOps diff viewers.
- Autonomous Fix Branch Generation: Automatically synthesize repair commits and open fix pull requests when non-deterministic or regression test failures are detected.

### Phase 4: LangGraph Parallel Orchestration & Context Optimization
- Hierarchical Sub-Graphs: Refactor LangGraph multi-agent architecture into parallel sub-graphs for concurrent AST search, impact analysis, and test generation.
- Dynamic Token Context Pruning: Optimize prompt context windows by filtering out non-essential AST nodes before LLM synthesis, reducing API costs and latency by 40%.
- Fine-Tuned Local LLM Support: Support self-hosted open-source coding LLMs (CodeLlama, DeepSeek-Coder, Qwen-Coder) via Ollama and vLLM backends.

### Phase 5: Enterprise Governance, Audit & RBAC
- Role-Based Access Control (RBAC): Enterprise permissions model (Admin, Developer, Auditor, Viewer).
- Security & Compliance Audit Logging: Log all repository connections, code indexing operations, AI test generations, and API token usage for SOC2/ISO27001 compliance.
- SAML 2.0 & Single Sign-On (SSO): Integrate Okta, Azure AD, and Keycloak authentication.
