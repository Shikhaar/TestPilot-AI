"use client";

import { use, useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { pullRequestsApi, PRDetail } from "@/lib/api/pullRequests";
import { testsApi, GeneratedTest } from "@/lib/api/tests";

export default function PRDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = params ? use(params) : { id: "pr-1" };
  const [pr, setPr] = useState<PRDetail | null>(null);
  const [generatedTests, setGeneratedTests] = useState<GeneratedTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"overview" | "review" | "graph" | "tests" | "failures" | "logs">("overview");
  
  // Real-time timeline states (Suggestion #12)
  const [timeline, setTimeline] = useState<Array<{ time: string; event: string; status: "completed" | "running" | "pending" }>>([
    { time: "09:31", event: "Webhook Received", status: "completed" },
    { time: "09:31", event: "Repository Cloned", status: "completed" },
    { time: "09:31", event: "Dependency Graph Built", status: "completed" },
    { time: "09:32", event: "Impacted Modules Found", status: "completed" },
    { time: "09:32", event: "Relevant Tests Found", status: "completed" },
    { time: "09:33", event: "Generated 8 New Tests", status: "completed" },
    { time: "09:34", event: "Running Tests", status: "running" },
    { time: "09:35", event: "Coverage Increased 11%", status: "pending" },
    { time: "09:35", event: "Review Posted", status: "pending" },
  ]);

  useEffect(() => {
    async function loadData() {
      try {
        const [prData, testData] = await Promise.all([
          pullRequestsApi.get(id),
          testsApi.getGeneratedTests(id),
        ]);
        setPr(prData);
        setGeneratedTests(testData.items);
      } catch (err) {
        console.error("Failed to load PR details, using mock fallback", err);
        setPr({
          id,
          repository_id: "repo-1",
          pr_number: 142,
          title: "feat: add secure secure-cookie token verification",
          state: "open",
          author: "dev-modern",
          base_branch: "main",
          head_branch: "feature/secure-cookie",
          analysis_status: "completed",
          risk_level: "medium",
          risk_score: 4.8,
          coverage_delta: 11.2,
          files_changed: 4,
          lines_added: 120,
          lines_removed: 15,
          created_at: new Date().toISOString(),
          affected_modules: ["app/core/security.py", "app/api/v1/auth.py"],
          risk_factors: ["Modifies authentication flow", "Adds secure cookies parameters"],
          review_summary: "Review drafted. No regression failures detected in core billing endpoints.",
        });
        setGeneratedTests([
          {
            id: "gen-1",
            file_path: "app/api/v1/auth.py",
            test_file_path: "tests/test_api/test_auth_cookie.py",
            function_name: "test_secure_cookie_refresh",
            class_name: null,
            test_type: "unit",
            test_framework: "pytest",
            status: "accepted",
            content: `
def test_secure_cookie_refresh(client, test_user):
    """Validate refresh token handles secure cookie credentials."""
    response = client.post("/api/v1/auth/refresh", cookies={"refresh_token": "valid_token"})
    assert response.status_code == 200
    assert "access_token" in response.json()
`,
            model_used: "gpt-4o-mini",
            created_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  // Handle WS messaging mock (Suggestion #9)
  useEffect(() => {
    if (loading) return;
    const interval = setTimeout(() => {
      setTimeline((prev) => {
        const next = [...prev];
        next[6].status = "completed";
        next[7].status = "completed";
        next[8].status = "completed";
        return next;
      });
    }, 4000);
    return () => clearTimeout(interval);
  }, [loading]);

  return (
    <div className="flex h-screen bg-[#030303]">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto px-10 py-8">
        {loading ? (
          <div className="flex justify-center py-24">
            <div className="w-10 h-10 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="space-y-8">
            {/* Header */}
            <header className="flex justify-between items-start">
              <div>
                <span className="text-xs text-purple-400 font-mono font-semibold">Pull Request #{pr?.pr_number}</span>
                <h1 className="text-xl font-bold mt-1">{pr?.title}</h1>
                <p className="text-xs text-gray-500 mt-1">
                  Author: <strong className="text-gray-300">{pr?.author}</strong> | 
                  Branches: <span className="font-mono text-purple-300">{pr?.head_branch}</span> ➔ <span className="font-mono text-gray-400">{pr?.base_branch}</span>
                </p>
              </div>
              <button
                onClick={async () => {
                  if (!pr) return;
                  await pullRequestsApi.postReview(pr.id);
                  alert("Review posted to GitHub!");
                }}
                className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold transition"
              >
                Post Review to GitHub
              </button>
            </header>

            {/* Navigation Tabs (Suggestion #5) */}
            <nav className="flex space-x-1 border-b border-white/5 pb-px">
              {(["overview", "review", "graph", "tests", "failures", "logs"] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 text-xs font-semibold border-b-2 capitalize transition-all ${
                    activeTab === tab
                      ? "border-purple-500 text-purple-400"
                      : "border-transparent text-gray-500 hover:text-gray-300"
                  }`}
                >
                  {tab === "graph" ? "Dependency Graph" : tab === "tests" ? "Generated Tests" : tab}
                </button>
              ))}
            </nav>

            {/* TAB CONTENTS */}
            <div className="mt-6">
              {/* Tab 1: Overview & PR Timeline */}
              {activeTab === "overview" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                  <div className="md:col-span-2 space-y-8">
                    {/* Risk Score Breakdown (Suggestion #8) */}
                    <div className="glass-panel p-6">
                      <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-6">Risk Score Breakdown</h3>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
                        <div className="flex flex-col items-center justify-center p-4 border border-white/5 rounded-lg bg-black/40">
                          <span className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Overall Risk</span>
                          <span className="text-3xl font-extrabold text-purple-400">4.8</span>
                        </div>
                        <div className="space-y-2 col-span-2">
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Authentication</span>
                            <span className="text-red-400 font-bold uppercase">HIGH</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Payments</span>
                            <span className="text-green-400 font-bold uppercase">LOW</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Code Coverage</span>
                            <span className="text-yellow-400 font-bold uppercase">MEDIUM</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Performance</span>
                            <span className="text-green-400 font-bold uppercase">LOW</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-gray-400">Database changes</span>
                            <span className="text-red-400 font-bold uppercase">HIGH</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* PR Metrics */}
                    <div className="grid grid-cols-3 gap-6">
                      <div className="glass-panel p-4">
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Files Changed</span>
                        <span className="text-lg font-bold">{pr?.files_changed}</span>
                      </div>
                      <div className="glass-panel p-4">
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Lines Added</span>
                        <span className="text-lg font-bold text-green-400">+{pr?.lines_added}</span>
                      </div>
                      <div className="glass-panel p-4">
                        <span className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Lines Deleted</span>
                        <span className="text-lg font-bold text-red-400">-{pr?.lines_removed}</span>
                      </div>
                    </div>
                  </div>

                  {/* Real-time PR Timeline sidebar (Suggestion #12) */}
                  <div className="glass-panel p-6">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-6">PR Timeline</h3>
                    <div className="relative border-l border-white/5 pl-4 ml-2 space-y-6">
                      {timeline.map((step, idx) => (
                        <div key={idx} className="relative">
                          <div className={`absolute -left-[21px] top-1.5 w-2 h-2 rounded-full border ${
                            step.status === "completed" ? "bg-green-500 border-green-500" :
                            step.status === "running" ? "bg-purple-500 border-purple-500 animate-ping" :
                            "bg-gray-800 border-gray-700"
                          }`} />
                          <div className="flex justify-between items-start text-xs">
                            <span className={`font-semibold ${step.status === "pending" ? "text-gray-600" : "text-gray-300"}`}>
                              {step.event}
                            </span>
                            <span className="font-mono text-gray-500 text-[10px]">{step.time}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Review Comments */}
              {activeTab === "review" && (
                <div className="glass-panel p-6 space-y-4">
                  <h2 className="text-base font-bold">Synthesized Review Body</h2>
                  <div className="p-4 border border-white/5 rounded-lg bg-black/40 font-mono text-xs text-gray-300 whitespace-pre-wrap">
                    {`🔍 Overview:
The PR introduces secure cookies parameters to authorization endpoints.

⚠️ Risk Assessment: MEDIUM (4.8/10.0)
- HIGH: Modifies auth routines.
- MEDIUM: Coverage gaps in secondary modules.

📋 Action Items:
- [ ] Ensure HTTPS is forced on all environments.
- [ ] Add unit test assertions checking Cookie attributes.`}
                  </div>
                </div>
              )}

              {/* Tab 3: Layered Dependency Graph */}
              {activeTab === "graph" && (
                <div className="glass-panel p-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">Architecture Layer Mapping</h3>
                  <div className="flex flex-col space-y-6 max-w-lg mx-auto py-8">
                    <div className="p-4 rounded-lg border border-purple-500/20 bg-purple-500/5 text-center text-xs font-mono">
                      Controllers / API Routes (auth.py)
                    </div>
                    <div className="flex justify-center">
                      <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 13l-7 7-7-7m14-6l-7 7-7-7" />
                      </svg>
                    </div>
                    <div className="p-4 rounded-lg border border-purple-500/20 bg-purple-500/5 text-center text-xs font-mono">
                      Core Services (github_service.py)
                    </div>
                    <div className="flex justify-center">
                      <svg className="w-5 h-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 13l-7 7-7-7m14-6l-7 7-7-7" />
                      </svg>
                    </div>
                    <div className="p-4 rounded-lg border border-purple-500/20 bg-purple-500/5 text-center text-xs font-mono">
                      Repositories & Models (user.py)
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Generated Tests (Suggestion #7) */}
              {activeTab === "tests" && (
                <div className="glass-panel p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400">Generated Tests</h3>
                    {/* Action Bar (Suggestion #7) */}
                    <div className="flex gap-2">
                      <button className="px-3 py-1.5 bg-green-600/10 hover:bg-green-600/20 border border-green-500/20 text-green-400 rounded text-xs font-semibold transition">
                        Accept
                      </button>
                      <button className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 rounded text-xs font-semibold transition">
                        Edit
                      </button>
                      <button className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded text-xs font-semibold transition">
                        Commit to Branch
                      </button>
                    </div>
                  </div>
                  
                  {generatedTests.map((test) => (
                    <div key={test.id} className="space-y-4">
                      <div className="text-xs text-gray-400">
                        Target File: <strong className="text-gray-300">{test.test_file_path}</strong>
                      </div>
                      <div className="p-4 border border-white/5 rounded-lg bg-black/40 font-mono text-xs text-gray-300 whitespace-pre">
                        {test.content}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 5: Failures / Analysis */}
              {activeTab === "failures" && (
                <div className="glass-panel p-6 space-y-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400">Failing Test Analysis</h3>
                  <div className="border border-red-500/20 bg-red-500/5 p-4 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-sm font-bold text-red-400">test_cookie_refresh_no_samesite</h4>
                      <span className="text-[10px] bg-red-500/10 border border-red-500/20 text-red-400 px-2 py-0.5 rounded uppercase font-bold">
                        92% confidence
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mb-4">
                      <strong>Root cause:</strong> Cookie response sets no SameSite directive, causing refresh validation failure on Chrome client agents.
                    </p>
                    <div className="p-3 border border-white/5 rounded bg-black/40 font-mono text-xs text-green-400">
                      {`# Suggested Fix:
response.set_cookie(..., samesite="lax")`}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 6: Logs */}
              {activeTab === "logs" && (
                <div className="glass-panel p-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">Execution logs</h3>
                  <div className="p-4 border border-white/5 rounded-lg bg-black/40 font-mono text-xs text-gray-500 h-96 overflow-y-auto">
                    {`[09:31:02] Hook received. Event type: pull_request
[09:31:15] Repository cloned to /tmp/repos/payment-gateway
[09:31:30] Tree-sitter parser completed. 14 files indexed.
[09:31:45] Dependency graph successfully built.
[09:32:01] 2 impacted modules identified.
[09:33:12] Generated 8 missing test assertions.
[09:34:02] Running regression test suite...
[09:35:10] Coverage increased: 84.6% (+11.2%)
[09:35:23] AI Review generated and posted.`}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
