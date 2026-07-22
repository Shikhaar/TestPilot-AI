"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { pullRequestsApi, PullRequest } from "@/lib/api/pullRequests";

export default function PullRequestsPage() {
  const [prs, setPrs] = useState<PullRequest[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filterState, setFilterState] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 15;

  useEffect(() => {
    async function loadPRs() {
      setLoading(true);
      try {
        // Fetch all PRs from API
        const data = await pullRequestsApi.list(undefined, filterState || undefined, page, pageSize).catch(() => null);
        if (data && data.items) {
          setPrs(data.items || []);
          setTotal(data.total || 0);
        } else {
          throw new Error("Backend offline - using mock PRs");
        }
      } catch {
        // Fallback mock data for preview mode
        // Fallback mock data
        const mockPRs: PullRequest[] = [
          {
            id: "pr-1",
            repository_id: "repo-1",
            pr_number: 142,
            title: "feat: add secure secure-cookie token verification",
            state: "open",
            author: "Shikhaar",
            base_branch: "main",
            head_branch: "feature/auth-cookies",
            analysis_status: "completed",
            risk_level: "medium",
            risk_score: 4.8,
            coverage_delta: 1.5,
            files_changed: 4,
            lines_added: 120,
            lines_removed: 15,
            created_at: new Date().toISOString(),
          },
          {
            id: "pr-2",
            repository_id: "repo-1",
            pr_number: 141,
            title: "fix: resolve race conditions on test runs queue",
            state: "open",
            author: "Shikhaar",
            base_branch: "main",
            head_branch: "bugfix/race-condition",
            analysis_status: "running",
            risk_level: "critical",
            risk_score: 8.5,
            coverage_delta: -0.8,
            files_changed: 2,
            lines_added: 45,
            lines_removed: 12,
            created_at: new Date().toISOString(),
          },
          {
            id: "pr-3",
            repository_id: "repo-2",
            pr_number: 89,
            title: "refactor: optimize AST parsing tree resolution",
            state: "closed",
            author: "collaborator-1",
            base_branch: "main",
            head_branch: "refactor/ast-tree",
            analysis_status: "completed",
            risk_level: "low",
            risk_score: 1.2,
            coverage_delta: 0.0,
            files_changed: 8,
            lines_added: 240,
            lines_removed: 310,
            created_at: new Date().toISOString(),
          }
        ];
        setPrs(mockPRs);
        setTotal(mockPRs.length);
      } finally {
        setLoading(false);
      }
    }

    loadPRs();
  }, [filterState, page]);

  // Filter client-side based on search query
  const filteredPRs = prs.filter(pr => 
    pr.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    pr.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
    pr.pr_number.toString().includes(searchQuery)
  );

  return (
    <div className="flex h-screen bg-[#030303]">
      <Sidebar />

      <main className="flex-1 overflow-y-auto px-10 py-8">
        {/* Header */}
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Pull Requests</h1>
            <p className="text-gray-500 text-sm">Monitor analysis history and code risk ratings</p>
          </div>
        </header>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <input
            type="text"
            placeholder="Search PR title, author, or number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
          />

          <select
            value={filterState}
            onChange={(e) => {
              setFilterState(e.target.value);
              setPage(1);
            }}
            className="px-4 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-sm text-gray-300 focus:outline-none focus:border-purple-500 transition-colors cursor-pointer"
          >
            <option value="">All States</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
            <option value="merged">Merged</option>
          </select>
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-10 h-10 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filteredPRs.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <svg className="w-12 h-12 text-gray-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4-4m-4 4l4 4" />
            </svg>
            <h3 className="text-lg font-semibold text-gray-300 mb-1">No Pull Requests Found</h3>
            <p className="text-sm text-gray-500">Connected repositories have not triggered any PR webhooks yet.</p>
          </div>
        ) : (
          <div className="glass-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-zinc-800 bg-zinc-900/50">
                    <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">PR Number</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Title</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Author</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Changes</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Risk Score</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-zinc-850">
                  {filteredPRs.map((pr) => {
                    const statusColors = {
                      pending: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
                      running: "bg-blue-500/10 text-blue-500 border-blue-500/20",
                      completed: "bg-green-500/10 text-green-500 border-green-500/20",
                      failed: "bg-red-500/10 text-red-500 border-red-500/20",
                    };

                    const riskColors = {
                      low: "text-green-500",
                      medium: "text-yellow-500",
                      high: "text-orange-500",
                      critical: "text-red-500",
                    };

                    return (
                      <tr key={pr.id} className="hover:bg-zinc-900/30 transition-colors">
                        <td className="px-6 py-4 text-sm font-semibold text-purple-400">
                          #{pr.pr_number}
                        </td>
                        <td className="px-6 py-4 text-sm font-medium text-gray-200">
                          <Link href={`/pull-requests/${pr.id}`} className="hover:underline">
                            {pr.title}
                          </Link>
                          <div className="text-xs text-gray-500 mt-1">
                            {pr.base_branch} 🡨 {pr.head_branch}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-400">
                          {pr.author}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-300">
                          <div className="flex gap-2 text-xs">
                            <span className="text-green-500">+{pr.lines_added}</span>
                            <span className="text-red-500">-{pr.lines_removed}</span>
                            <span className="text-gray-500">({pr.files_changed} files)</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm font-bold">
                          {pr.risk_score !== null ? (
                            <span className={riskColors[pr.risk_level as keyof typeof riskColors] || "text-gray-400"}>
                              {pr.risk_score.toFixed(1)} / 10
                            </span>
                          ) : (
                            <span className="text-gray-500">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${statusColors[pr.analysis_status] || "bg-zinc-500/10 text-gray-400 border-zinc-500/20"}`}>
                            {pr.analysis_status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <Link
                            href={`/pull-requests/${pr.id}`}
                            className="inline-flex items-center text-xs font-semibold text-purple-400 hover:text-purple-300 hover:underline"
                          >
                            View Details 🡪
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {total > pageSize && (
              <div className="flex justify-between items-center px-6 py-4 border-t border-zinc-800 bg-zinc-900/30">
                <span className="text-xs text-gray-500">
                  Showing {filteredPRs.length} of {total} PRs
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={page === 1}
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    className="px-3 py-1.5 rounded bg-zinc-800 text-xs font-medium text-gray-400 hover:bg-zinc-700 disabled:opacity-50 transition-colors"
                  >
                    Previous
                  </button>
                  <button
                    disabled={page * pageSize >= total}
                    onClick={() => setPage(p => p + 1)}
                    className="px-3 py-1.5 rounded bg-zinc-800 text-xs font-medium text-gray-400 hover:bg-zinc-700 disabled:opacity-50 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
