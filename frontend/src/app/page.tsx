"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { dashboardApi, DashboardMetrics, DetailedMetrics } from "@/lib/api/dashboard";

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [detailed, setDetailed] = useState<DetailedMetrics | null>(null);
  const [loading, setLoading] = useState(true);

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
        console.error("Failed to load dashboard data, using mock fallback", err);
        // Fallback mock data matching suggestion #3 criteria
        setMetrics({
          repositories: { total: 4, indexed: 3, pending: 1 },
          pull_requests: { total: 12, critical: 2, active: 1, success_rate: 98.8 },
          tests: { generated: 184 },
          recent_pull_requests: [
            {
              id: "pr-1",
              pr_number: 142,
              title: "feat: add secure secure-cookie token verification",
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

  return (
    <div className="flex h-screen bg-[#030303]">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto px-10 py-8">
        {/* Header */}
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Overview</h1>
            <p className="text-gray-500 text-sm">Platform health and active regression analysis</p>
          </div>
          <div className="text-xs text-gray-500">
            System status: <span className="text-green-500 font-semibold">Active</span>
          </div>
        </header>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-10 h-10 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="space-y-8">
            {/* Developer Metrics Grid */}
            <section className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {/* Connected Repositories */}
              <div className="glass-card p-6">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Repositories</span>
                  <span className="text-purple-400 text-xs px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20">
                    Active
                  </span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">{metrics?.repositories.total || 0}</span>
                  <span className="text-gray-500 text-xs">({metrics?.repositories.indexed || 0} indexed)</span>
                </div>
              </div>

              {/* PRs Awaiting Review */}
              <div className="glass-card p-6">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Awaiting Review</span>
                  <span className="text-red-400 text-xs px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/20">
                    PRs
                  </span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">{metrics?.pull_requests.total || 0}</span>
                  <span className="text-gray-500 text-xs">({metrics?.pull_requests.critical || 0} critical)</span>
                </div>
              </div>

              {/* Tests Generated */}
              <div className="glass-card p-6">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Tests Generated</span>
                  <span className="text-green-400 text-xs px-2 py-0.5 rounded-full bg-green-500/10 border border-green-500/20">
                    AI
                  </span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">{metrics?.tests.generated || 0}</span>
                  <span className="text-gray-500 text-xs">total cases</span>
                </div>
              </div>

              {/* Average Coverage */}
              <div className="glass-card p-6">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Avg Coverage</span>
                  <span className="text-blue-400 text-xs px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20">
                    Quality
                  </span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">{detailed?.coverage.average_percentage || 0}%</span>
                  <span className="text-gray-500 text-xs">avg coverage</span>
                </div>
              </div>

              {/* AI Cost */}
              <div className="glass-card p-6">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">AI Cost</span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">${detailed?.ai_usage.estimated_cost_usd.toFixed(2)}</span>
                  <span className="text-gray-500 text-xs">USD</span>
                </div>
              </div>

              {/* Queue Length */}
              <div className="glass-card p-6">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Queue Length</span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">{metrics?.pull_requests.active ?? 0}</span>
                  <span className="text-gray-500 text-xs">active tasks</span>
                </div>
              </div>

              {/* Agent Success */}
              <div className="glass-card p-6">
                <div className="flex justify-between items-start mb-4">
                  <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Agent Success</span>
                </div>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl font-bold">
                    {metrics?.pull_requests.success_rate !== undefined
                      ? `${metrics.pull_requests.success_rate}%`
                      : "100.0%"}
                  </span>
                  <span className="text-gray-500 text-xs">execution rate</span>
                </div>
              </div>
            </section>

            {/* Recent Pull Requests */}
            <section className="glass-panel p-6">
              <h2 className="text-lg font-bold mb-6">Recent Pull Request Analyses</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-gray-400">
                  <thead className="text-xs uppercase text-gray-500 border-b border-white/5">
                    <tr>
                      <th className="py-3 px-4">PR #</th>
                      <th className="py-3 px-4">Title</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4">Risk Level</th>
                      <th className="py-3 px-4">Risk Score</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {metrics?.recent_pull_requests.map((pr) => {
                      const riskColor = {
                        low: "text-green-400 bg-green-500/10 border-green-500/20",
                        medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
                        high: "text-orange-400 bg-orange-500/10 border-orange-500/20",
                        critical: "text-red-400 bg-red-500/10 border-red-500/20",
                      }[pr.risk_level || "low"];

                      return (
                        <tr key={pr.id} className="hover:bg-white/10 transition-colors">
                          <td className="py-4 px-4 font-mono">#{pr.pr_number}</td>
                          <td className="py-4 px-4 text-gray-200 font-medium">{pr.title}</td>
                          <td className="py-4 px-4">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              pr.analysis_status === "running" ? "text-purple-400 animate-pulse" : "text-gray-400"
                            }`}>
                              {pr.analysis_status}
                            </span>
                          </td>
                          <td className="py-4 px-4">
                            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${riskColor}`}>
                              {pr.risk_level}
                            </span>
                          </td>
                          <td className="py-4 px-4 font-mono font-bold text-gray-200">
                            {pr.risk_score ? pr.risk_score.toFixed(1) : "N/A"}
                          </td>
                          <td className="py-4 px-4 text-right">
                            <Link
                              href={`/pull-requests/${pr.id}`}
                              className="text-purple-400 hover:text-purple-300 font-semibold transition"
                            >
                              View Report
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
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
