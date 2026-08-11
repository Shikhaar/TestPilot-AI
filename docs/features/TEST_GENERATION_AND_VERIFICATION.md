# Test Generation & Verification Architecture

TestPilot AI does not rely solely on static analysis or unverified LLM output. Instead, it executes generated tests inside an isolated sandbox (for supported frameworks such as `pytest`, `jest`, `go test`, and `mvn test`) and analyzes actual runtime execution results.

---

## 1. Detecting Pass vs. Fail (`execution_agent`)

During execution, TestPilot AI collects multiple execution signals directly from the operating system and test runners:

### Subprocess Exit Codes
- **Exit code `0`**: Test suite completed successfully.
- **Non-zero exit code**: One or more tests failed or the execution process crashed.

### Structured Test Reports
When supported by the test framework, TestPilot AI executes tests with machine-readable reporting enabled:
- **Pytest**: `python -m pytest --json-report --json-report-file=/tmp/testpilot_report.json`
- **Jest**: `npx jest --json --outputFile=/tmp/testpilot_jest.json`

These reports are parsed to extract:
- Total number of passed, failed, skipped, and errored tests.
- Individual test function names and execution durations.
- Failure messages and metadata.

### Coverage Metrics (Optional)
When coverage collection is enabled (`pytest-cov`, `jest --coverage`), TestPilot AI records line and branch coverage metrics to evaluate how thoroughly the generated tests exercise the codebase.

### Runtime Logs and Stack Traces
For failing tests, TestPilot AI captures:
- Failed test name and file location.
- Exception type (e.g., `AssertionError`, `ModuleNotFoundError`, `TypeError`).
- Complete stack trace.
- Standard output (`stdout`) and error streams (`stderr`).

---

## 2. Auto-Healing Loop (`failure_analysis_agent`)

When a test fails, `execution_agent` forwards a structured failure report to `failure_analysis_agent`:

```json
{
 "test_name": "test_auth_header",
 "error": "ModuleNotFoundError: No module named 'app.utils.crypto'",
 "stack_trace": "File 'tests/test_auth.py', line 12...",
 "source_code": "from app.utils.crypto import hash_token"
}
```

### The Self-Healing Workflow:
1. **Root Cause Analysis**: Identifies the likely root cause from the stack trace and source code (e.g., outdated import path, missing mock, incorrect fixture).
2. **Test Code Regeneration**: Generates an updated version of the failing test or its mocks.
3. **Re-Execution & Verification**: Re-executes the modified tests in the sandbox.
4. **Iterative Verification**: Repeats the process until the tests pass or the 3-attempt retry limit is reached (`Pass@N` benchmark of 98.1%).

---

## 3. Graceful Fallback Mechanism & Retry Limits

If a generated test cannot be automatically repaired after 3 attempts (e.g., due to a real pre-existing bug in the PR source code, missing external service credentials, or complex multi-layered mock requirements), TestPilot AI handles the failure gracefully:

1. **Warning Label Flag**: The test is tagged with a `Generation Warning / Unverified` status in the PR review comment and UI dashboard.
2. **Failure Analysis Diagnostic Report**: The system outputs a structured Failure Analysis Report detailing:
   - Root Cause analysis
   - Affected code path
   - PR Regression Classification (whether the failure was introduced by the PR changes)
   - Confidence score (0.0 - 1.0)
3. **Actionable Fix Suggestions**: The unverified test code is displayed alongside a suggested fix recommendation, empowering developers to review the edge case and decide whether to update their source code logic or adjust the test fixture manually.
