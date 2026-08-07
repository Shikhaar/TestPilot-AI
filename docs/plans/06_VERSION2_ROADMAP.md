# TestPilot AI — Version 2.0.0 Implementation Plan

TestPilot AI Version 2 (v2.0.0) expands the platform into an enterprise-grade, multi-tenant AI software engineering suite featuring native monorepo graph resolution, real-time webhooks across all VCS providers, sandboxed containerized test execution, and automated pull request auto-remediation.

---

## Technical Goals & Architecture Milestones

### Phase 1: Native Monorepo Support & Enterprise Webhooks
- Multi-Package AST Graph Resolution: Extend Tree-sitter dependency parsing to support monorepos containing multiple independent service directories (npm workspaces, Lerna, Nx, Cargo workspaces, Go modules).
- Unified Webhook Receiver: Expand webhook endpoints (`/api/v1/webhooks/*`) to process pull request events, commit pushes, and comment triggers from Bitbucket, GitLab, and Azure DevOps in addition to GitHub.
- Scope-Based Indexing: Allow selective AST vector indexing for sub-directories and individual microservices within large repositories.

### Phase 2: Sandboxed Ephemeral Test Execution Engine
- Isolated Container Runner: Execute generated Pytest, Vitest, Jest, Go, and JUnit test suites inside ephemeral Docker / WebAssembly sandbox containers to guarantee zero host pollution and secure execution.
- Security Policy Enforcement: Enforce memory limits, CPU quotas, network isolation, and execution timeouts on test runs.
- Cross-Language Test Adapters: Add native test execution adapters for Go (`go test`), Java (`JUnit 5`), Rust (`cargo test`), and C# (`dotnet test`).

### Phase 3: Automated Pull Request Auto-Remediation
- Auto-Fix Branch Push: Enable AI agents to automatically commit synthesized unit test files and code fix patches back to target branches on GitHub, Bitbucket, GitLab, and Azure DevOps.
- Inline Code Annotations: Post line-level inline code review comments and suggested fixes directly inside pull request diff viewers.
- Flaky Test Detection & Auto-Healing: Automatically re-run failed test suites across multiple seeds and push repair commits when non-deterministic behavior is resolved.

### Phase 4: LangGraph Parallel Orchestration & Context Optimization
- Hierarchical Sub-Graphs: Refactor LangGraph multi-agent architecture into parallel sub-graphs for concurrent AST search, impact analysis, and test generation.
- Dynamic Token Context Pruning: Optimize prompt context windows by filtering out non-essential AST nodes before LLM synthesis, reducing API costs and latency by 40%.
- Fine-Tuned Local LLM Support: Support self-hosted open-source coding LLMs (CodeLlama, DeepSeek-Coder, Qwen-Coder) via Ollama and vLLM backends.

### Phase 5: Enterprise Governance, Audit & RBAC
- Role-Based Access Control (RBAC): Enterprise permissions model (Admin, Developer, Auditor, Viewer).
- Security & Compliance Audit Logging: Log all repository connections, code indexing operations, AI test generations, and API token usage for SOC2/ISO27001 compliance.
- SAML 2.0 & Single Sign-On (SSO): Integrate Okta, Azure AD, and Keycloak authentication.
