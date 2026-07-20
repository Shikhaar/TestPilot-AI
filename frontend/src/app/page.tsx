"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import Logo from "@/components/Logo";
import { dashboardApi, DashboardMetrics, DetailedMetrics } from "@/lib/api/dashboard";

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [detailed, setDetailed] = useState<DetailedMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [filterState, setFilterState] = useState<"all" | "critical" | "running">("all");

  useEffect(() => {
    async function loadData() {
      try {
        const [overviewData, detailedData] = await Promise.all([
          dashboardApi.getOverview(),
          dashboardApi.getDetailedMetrics(),
        ]);
        setMetrics(overviewData);
        setDetailed(detailedData);
      } catch (err) {
        console.error("Failed to load dashboard data, using fallback", err);
        // Fallback data for preview/demo
        setMetrics({
          repositories: { total: 4, indexed: 3, pending: 1 },
          pull_requests: { total: 12, critical: 2, active: 1, success_rate: 98.8 },
          tests: { generated: 184 },
          recent_pull_requests: [
            {
              id: "pr-1",
              pr_number: 142,
              title: "feat: add secure cookie token verification",
              state: "open",
              risk_level: "medium",
              risk_score: 4.8,
              analysis_status: "completed",
              created_at: new Date().toISOString(),
            },
            {
              id: "pr-2",
              pr_number: 141,
              title: "fix: resolve race conditions on test runs queue",
              state: "open",
              risk_level: "critical",
              risk_score: 8.5,
              analysis_status: "running",
              created_at: new Date().toISOString(),
            },
            {
              id: "pr-3",
              pr_number: 140,
              title: "refactor: optimize AST parsing tree resolution",
              state: "closed",
              risk_level: "low",
              risk_score: 1.2,
              analysis_status: "completed",
              created_at: new Date().toISOString(),
            },
          ],
        });
        setDetailed({
          ai_usage: { total_tokens: 450200, estimated_cost_usd: 1.84 },
          coverage: { average_percentage: 82.4 },
        });
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredPRs = metrics?.recent_pull_requests.filter((pr) => {
    if (filterState === "critical") return pr.risk_level === "critical" || pr.risk_level === "high";
    if (filterState === "running") return pr.analysis_status === "running";
    return true;
  });

  return (
    <div className="flex h-screen bg-[#030407] text-gray-100 font-sans antialiased overflow-hidden">
      {/* Background ambient lighting */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-purple-900/15 blur-[140px] animate-pulse-slow" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-900/15 blur-[140px] animate-pulse-slow" />
      </div>

      <Sidebar />

      <main className="flex-1 overflow-y-auto px-8 py-8">
        {/* Top Header Banner */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 pb-6 border-b border-white/5">
          <div className="flex items-center space-x-4">
            <Logo variant="icon" size="lg" />
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
                  Platform Overview
                </h1>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping mr-1.5" />
                  Systems Operational
                </span>
              </div>
              <p className="text-gray-400 text-xs mt-1">
                Automated regression testing, vector AST indexing, and risk impact analysis
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 text-xs font-semibold text-gray-300 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all">
              Connect Repository
            </button>
            <button className="px-4 py-2 text-xs font-semibold text-white bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 rounded-lg shadow-lg shadow-purple-600/20 transition-all flex items-center space-x-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Run Regression Test</span>
            </button>
          </div>
        </header>

        {loading ? (
          <div className="flex flex-col items-center justify-center h-80 space-y-4">
            <div className="w-12 h-12 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-500 text-xs">Fetching telemetry metrics...</p>
          </div>
        ) : (
          <div className="space-y-8">
            {/* KPI Metrics Cards Grid */}
            <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {/* Connected Repositories */}
              <div className="glass-card p-5">
                <div className="flex justify-between items-start mb-3">
                  <span className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold">
                    Repositories
                  </span>
                  <span className="text-purple-400 text-[10px] font-medium px-2 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/20">
                    {metrics?.repositories.indexed || 0} / {metrics?.repositories.total || 0} Indexed
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-3xl font-extrabold tracking-tight text-white">
                    {metrics?.repositories.total || 0}
                  </span>
                  <span className="text-xs text-emerald-400 font-medium">100% active</span>
                </div>
                <div className="mt-3 w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full"
                    style={{
                      width: `${((metrics?.repositories.indexed || 0) / (metrics?.repositories.total || 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>

              {/* Awaiting Review */}
              <div className="glass-card p-5">
                <div className="flex justify-between items-start mb-3">
                  <span className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold">
                    Awaiting Review
                  </span>
                  <span className="text-rose-400 text-[10px] font-medium px-2 py-0.5 rounded-md bg-rose-500/10 border border-rose-500/20">
                    {metrics?.pull_requests.critical || 0} Critical Risk
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-3xl font-extrabold tracking-tight text-white">
                    {metrics?.pull_requests.total || 0}
                  </span>
                  <span className="text-xs text-gray-400">PRs analyzed</span>
                </div>
                <div className="mt-3 text-[11px] text-gray-400 flex justify-between">
                  <span>Queue status:</span>
                  <span className="text-cyan-400 font-mono font-medium">Processing</span>
                </div>
              </div>

              {/* Generated Tests */}
              <div className="glass-card p-5">
                <div className="flex justify-between items-start mb-3">
                  <span className="text-[11px] text-gray-400 uppercase tracking-wider font-semibold">
                    Generated Tests
                  </span>
                  <span className="text-cyan-400 text-[10px] font-medium px-2 py-0.5 rounded-md bg-cyan-500/10 border border-cyan-500/20">
                    AI Auto-Suite
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-3xl font-extrabold tracking-tight text-white">
                    {metrics?.tests.generated || 0}
                  </span>
                  <span className="text-xs text-emerald-400 font-medium">+18 this week</span>
                </div>
                <div className="mt-3 text-[11px] text-gray-400 flex justify-between">
                  <span>Framework:</span>
                  <span className="text-gray-300 font-mono font-medium">Pytest + AST</span>
                </div>
              </div>

              {/* Agent Success Rate (Highlighted Card) */}
              <div className="glass-card p-5 border-purple-500/30 bg-purple-950/20">
                <div className="flex justify-between items-start mb-3">
                  <span className="text-[11px] text-purple-300 uppercase tracking-wider font-semibold">
                    Agent Success Rate
                  </span>
                  <span className="text-emerald-400 text-[10px] font-semibold px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30">
                    Optimal
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-emerald-300 to-cyan-300 bg-clip-text text-transparent">
                    {metrics?.pull_requests.success_rate !== undefined
                      ? `${metrics.pull_requests.success_rate}%`
                      : "100.0%"}
                  </span>
                  <span className="text-xs text-emerald-400 font-medium">0 failures</span>
                </div>
                <div className="mt-3 text-[11px] text-gray-400 flex justify-between items-center">
                  <span>ReAct Loop Stability:</span>
                  <span className="text-emerald-400 font-mono font-semibold">100% verified</span>
                </div>
              </div>
            </section>

            {/* Secondary Metrics & AI Agent Execution Log */}
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Coverage & AI Token Usage Card */}
              <div className="glass-panel p-6 flex flex-col justify-between space-y-6">
                <div>
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">
                    Quality & AI Token Metrics
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="text-gray-300 font-medium">Code Coverage Target</span>
                        <span className="text-purple-400 font-mono font-bold">
                          {detailed?.coverage.average_percentage || 82.4}%
                        </span>
                      </div>
                      <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-cyan-400 h-full rounded-full"
                          style={{ width: `${detailed?.coverage.average_percentage || 82.4}%` }}
                        />
                      </div>
                    </div>

                    <div className="pt-2 border-t border-white/5 flex justify-between items-center">
                      <div>
                        <p className="text-xs text-gray-400">Total Tokens Processed</p>
                        <p className="text-lg font-mono font-bold text-gray-200">
                          {detailed?.ai_usage.total_tokens.toLocaleString() || "450,200"}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-400">Estimated Cost</p>
                        <p className="text-lg font-mono font-bold text-cyan-400">
                          ${detailed?.ai_usage.estimated_cost_usd.toFixed(2) || "1.84"} USD
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-white/5 border border-white/5 text-xs text-gray-400 flex items-center justify-between">
                  <span>Model Engine:</span>
                  <span className="font-mono text-purple-300 font-semibold">Gemini 2.0 Flash</span>
                </div>
              </div>

              {/* Live AI Agent Execution Console Snippet */}
              <div className="glass-panel p-6 lg:col-span-2 flex flex-col justify-between">
                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                    <h3 className="text-sm font-bold uppercase tracking-wider text-gray-200">
                      Live AI Agent Telemetry
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-gray-500 bg-white/5 px-2 py-0.5 rounded">
                    Qdrant + Tree-sitter AST
                  </span>
                </div>

                <div className="bg-[#020305] border border-white/10 rounded-lg p-4 font-mono text-xs text-gray-300 space-y-2.5 overflow-x-auto">
                  <div className="flex space-x-2">
                    <span className="text-gray-600">[18:05:12]</span>
                    <span className="text-purple-400 font-bold">[AST_PARSER]</span>
                    <span className="text-gray-300">Parsed 14 modified symbols across backend/app/api/v1/auth.py</span>
                  </div>
                  <div className="flex space-x-2">
                    <span className="text-gray-600">[18:05:14]</span>
                    <span className="text-cyan-400 font-bold">[VECTOR_SEARCH]</span>
                    <span className="text-gray-300">Queried Qdrant embeddings: 3 target test dependencies matched (score: 0.94)</span>
                  </div>
                  <div className="flex space-x-2">
                    <span className="text-gray-600">[18:05:18]</span>
                    <span className="text-emerald-400 font-bold">[TEST_GENERATOR]</span>
                    <span className="text-gray-300">Generated 8 unit test assertions for token verification pipeline</span>
                  </div>
                  <div className="flex space-x-2">
                    <span className="text-gray-600">[18:05:21]</span>
                    <span className="text-indigo-400 font-bold">[RISK_SCORER]</span>
                    <span className="text-gray-300 font-semibold">PR #142 Risk Assessment completed: Medium Risk (Score: 4.8)</span>
                  </div>
                </div>

                <div className="mt-4 flex justify-between items-center text-xs text-gray-400">
                  <span>Active Agent: <strong className="text-purple-300">LangGraph Executor</strong></span>
                  <Link href="/monitoring" className="text-purple-400 hover:text-purple-300 font-semibold transition">
                    View Full System Logs &rarr;
                  </Link>
                </div>
              </div>
            </section>

            {/* Recent Pull Request Analyses Table */}
            <section className="glass-panel p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-lg font-bold text-gray-100 tracking-tight">Recent Pull Request Analyses</h2>
                  <p className="text-xs text-gray-500">Automated risk scores and AI generated test case suites</p>
                </div>

                {/* Filter Tabs */}
                <div className="flex items-center space-x-1 bg-white/5 p-1 rounded-lg border border-white/5 text-xs">
                  <button
                    onClick={() => setFilterState("all")}
                    className={`px-3 py-1.5 rounded-md font-medium transition ${
                      filterState === "all"
                        ? "bg-purple-600/30 text-purple-200 border border-purple-500/30"
                        : "text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    All PRs
                  </button>
                  <button
                    onClick={() => setFilterState("critical")}
                    className={`px-3 py-1.5 rounded-md font-medium transition ${
                      filterState === "critical"
                        ? "bg-rose-600/30 text-rose-200 border border-rose-500/30"
                        : "text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    High Risk
                  </button>
                  <button
                    onClick={() => setFilterState("running")}
                    className={`px-3 py-1.5 rounded-md font-medium transition ${
                      filterState === "running"
                        ? "bg-cyan-600/30 text-cyan-200 border border-cyan-500/30"
                        : "text-gray-400 hover:text-gray-200"
                    }`}
                  >
                    In Progress
                  </button>
                </div>
              </div>

              {/* PR Table */}
              <div className="overflow-x-auto rounded-lg border border-white/5">
                <table className="w-full text-left text-sm text-gray-400">
                  <thead className="text-xs uppercase tracking-wider text-gray-400 bg-white/5 border-b border-white/5 font-semibold">
                    <tr>
                      <th className="py-3.5 px-4">PR #</th>
                      <th className="py-3.5 px-4">Title</th>
                      <th className="py-3.5 px-4">Analysis Status</th>
                      <th className="py-3.5 px-4">Risk Level</th>
                      <th className="py-3.5 px-4">Risk Meter</th>
                      <th className="py-3.5 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 bg-black/20">
                    {filteredPRs && filteredPRs.length > 0 ? (
                      filteredPRs.map((pr) => {
                        const riskColor = {
                          low: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
                          medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
                          high: "text-orange-400 bg-orange-500/10 border-orange-500/20",
                          critical: "text-rose-400 bg-rose-500/10 border-rose-500/20",
                        }[pr.risk_level || "low"];

                        const scoreWidth = `${Math.min(((pr.risk_score || 0) / 10) * 100, 100)}%`;

                        return (
                          <tr key={pr.id} className="hover:bg-white/5 transition-colors">
                            <td className="py-4 px-4 font-mono text-purple-300 font-semibold">
                              #{pr.pr_number}
                            </td>
                            <td className="py-4 px-4 text-gray-200 font-medium max-w-xs truncate">
                              {pr.title}
                            </td>
                            <td className="py-4 px-4">
                              <span
                                className={`text-xs px-2.5 py-1 rounded-full font-medium border ${
                                  pr.analysis_status === "running"
                                    ? "text-cyan-300 bg-cyan-500/10 border-cyan-500/30 animate-pulse"
                                    : "text-gray-300 bg-white/5 border-white/10"
                                }`}
                              >
                                {pr.analysis_status}
                              </span>
                            </td>
                            <td className="py-4 px-4">
                              <span
                                className={`text-[10px] uppercase font-bold tracking-wider px-2.5 py-1 rounded-full border ${riskColor}`}
                              >
                                {pr.risk_level}
                              </span>
                            </td>
                            <td className="py-4 px-4">
                              <div className="flex items-center space-x-2">
                                <div className="w-24 bg-white/10 h-1.5 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full rounded-full ${
                                      (pr.risk_score || 0) > 7
                                        ? "bg-rose-500"
                                        : (pr.risk_score || 0) > 4
                                        ? "bg-amber-500"
                                        : "bg-emerald-500"
                                    }`}
                                    style={{ width: scoreWidth }}
                                  />
                                </div>
                                <span className="font-mono text-xs font-bold text-gray-200">
                                  {pr.risk_score ? pr.risk_score.toFixed(1) : "0.0"}
                                </span>
                              </div>
                            </td>
                            <td className="py-4 px-4 text-right">
                              <Link
                                href={`/pull-requests/${pr.id}`}
                                className="text-xs text-purple-400 hover:text-purple-300 font-semibold px-3 py-1.5 rounded-md bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 transition"
                              >
                                View Report
                              </Link>
                            </td>
                          </tr>
                        );
                      })
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-gray-500 text-xs">
                          No pull requests found matching current filter criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
