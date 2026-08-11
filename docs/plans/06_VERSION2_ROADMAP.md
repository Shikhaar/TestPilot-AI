# TestPilot AI — Version 2.0.0 Architecture Roadmap (Planned — To Be Done Later)

TestPilot AI Version 2 (v2.0.0) will expand the platform into an enterprise-grade AI software engineering suite featuring Docker containerized test execution, autonomous pull request auto-remediation, and enterprise RBAC compliance logging.

---

## Technical Goals & Architecture Milestones

### Phase 1: Docker Containerized Test Sandbox & Isolation
- Host Subprocess to Docker Sandbox Migration: Transition test execution in `execution_agent_node` (`backend/app/agents/execution_agent.py`) from local host `subprocess.run()` calls to isolated ephemeral Docker sandbox containers (`docker run --rm --network none --memory=2g`).
- Sandbox Security Policy Enforcement: Enforce memory limits, CPU quotas, filesystem read-only locks, network isolation, and execution timeouts to protect host infrastructure from malicious or runaway test code.
- Multi-Language Runtime Images: Add pre-built runner images for Python (pytest), Node.js (jest/vitest), Go (`go test`), Java (`mvn test`), and Rust (`cargo test`).

### Phase 2: Automated Pull Request Auto-Remediation & Inline Annotations
- Manual Commit Button to Autonomous Remediation: Upgrade from manual UI test commitment (`POST /repositories/{id}/commit-tests`) to autonomous AI agent patch commits on target branches (`testpilot/fix-<pr-id>`).
- Inline Line-Level PR Annotations: Transition top-level PR summary comments into line-by-line inline code annotations on GitHub, Bitbucket, GitLab, and Azure DevOps diff viewers.
- Autonomous Fix Branch Generation: Automatically synthesize repair commits and open fix pull requests when non-deterministic or regression test failures are detected.

### Phase 3: Enterprise Governance, Audit Logging & RBAC
- Role-Based Access Control (RBAC): Enterprise permissions model (Admin, Developer, Auditor, Viewer).
- Security & Compliance Audit Logging: Log all repository connections, code indexing operations, AI test generations, and API token usage for SOC2/ISO27001 compliance.
- SAML 2.0 & Single Sign-On (SSO): Integrate Okta, Azure AD, and Keycloak authentication.
