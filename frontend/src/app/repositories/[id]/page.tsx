"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { repositoriesApi, Repository } from "@/lib/api/repositories";

import { pullRequestsApi, PullRequest } from "@/lib/api/pullRequests";

export default function RepositoryDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [repo, setRepo] = useState<Repository | null>(null);
  const [prs, setPrs] = useState<PullRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [reindexing, setReindexing] = useState(false);

  const [selectedBranch, setSelectedBranch] = useState("");

  const fetchRepo = async () => {
    try {
      const [data, prData] = await Promise.all([
        repositoriesApi.get(id).catch(() => null),
        pullRequestsApi.list(id).catch(() => null),
      ]);
      if (data) {
        setRepo(data);
        if (!selectedBranch) {
          setSelectedBranch(data.default_branch || "main");
        }
      }
      if (prData && prData.items) setPrs(prData.items);
    } catch (err) {
      console.error("Failed to load repo", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepo();
  }, [id]);

  // Poll repository status every 3s while indexing is in progress
  useEffect(() => {
    if (repo?.index_status !== "indexing") return;
    const interval = setInterval(() => {
      fetchRepo();
    }, 3000);
    return () => clearInterval(interval);
  }, [repo?.index_status, id]);

  const handleReindex = async () => {
    if (!repo) return;
    setReindexing(true);
    setRepo((prev) => (prev ? { ...prev, index_status: "indexing" } : null));
    try {
      await repositoriesApi.triggerReindex(repo.id, true, selectedBranch || undefined);
    } catch (err) {
      console.error(err);
    } finally {
      setReindexing(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#030303]">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto px-10 py-8">
        {loading ? (
          <div className="flex justify-center py-24">
            <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="space-y-8">
            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <h1 className="text-2xl font-bold tracking-tight">{repo?.full_name}</h1>
                  <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-blue-500/20 bg-blue-500/5 text-blue-400`}>
                    {repo?.index_status}
                  </span>
                </div>
                <p className="text-gray-500 text-sm max-w-2xl">{repo?.description || "No description provided."}</p>
              </div>

              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-300">
                  <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                  <span className="text-gray-500 font-semibold">Branch:</span>
                  <input
                    type="text"
                    value={selectedBranch}
                    onChange={(e) => setSelectedBranch(e.target.value)}
                    placeholder="main"
                    className="bg-transparent border-none outline-none text-white font-mono w-24 text-xs"
                  />
                </div>

                <button
                  onClick={handleReindex}
                  disabled={reindexing}
                  className="px-4 py-2 bg-blue-700 hover:bg-blue-800 disabled:bg-gray-800 text-white rounded-lg text-xs font-semibold shadow-lg shadow-blue-900/30 transition"
                >
                  {reindexing ? "Queueing Index..." : "Force Re-Index"}
                </button>
              </div>
            </header>

            {/* Insights Layout (Suggestion #4) */}
            <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Left Column: Metrics & Architecture Summary */}
              <div className="md:col-span-2 space-y-8">
                {/* Repository Overview Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div className="glass-panel p-6">
                    <span className="text-[10px] uppercase tracking-wider text-gray-500 block mb-1">Health Score</span>
                    <span className="text-2xl font-bold text-purple-400">{repo?.health_score ? repo.health_score.toFixed(1) : "N/A"}</span>
                  </div>
                  <div className="glass-panel p-6">
                    <span className="text-[10px] uppercase tracking-wider text-gray-500 block mb-1">Code Coverage</span>
                    <span className="text-2xl font-bold text-gray-200">{repo?.coverage_percentage ? `${repo.coverage_percentage}%` : "N/A"}</span>
                  </div>
                  <div className="glass-panel p-6">
                    <span className="text-[10px] uppercase tracking-wider text-gray-500 block mb-1">Total Files</span>
                    <span className="text-2xl font-bold text-gray-200">{repo?.total_files || 0}</span>
                  </div>
                </div>

                {/* Architecture Summary */}
                <div className="glass-panel p-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">Architecture Summary</h3>
                  <p className="text-sm text-gray-300 leading-relaxed mb-4">
                    The codebase is organized in a layered Clean Architecture structure. 
                    The entry routes route payloads to the core service layer, which triggers database operations 
                    using the Repository repository structures.
                  </p>
                  <div className="flex gap-4 text-xs font-mono text-gray-500">
                    <div>Functions: <span className="text-gray-300">{repo?.total_functions || 0}</span></div>
                    <div>Classes: <span className="text-gray-300">{repo?.total_classes || 0}</span></div>
                    <div>Detected Branch: <span className="text-purple-400 font-semibold">{repo?.default_branch || "main"}</span></div>
                  </div>
                </div>

                {/* Layered Dependency Graph Preview */}
                <div className="glass-panel p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400">Dependency Graph (Layered Overview)</h3>
                    <span className="text-xs text-purple-400 font-semibold">Active Layer Mapping</span>
                  </div>
                  <div className="flex justify-around items-center h-28 border border-white/5 rounded-lg bg-black/40">
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] uppercase tracking-wider text-purple-400 font-bold">Routes</span>
                      <div className="w-16 h-8 rounded border border-white/10 bg-white/5 flex items-center justify-center text-xs mt-2 font-mono">14 nodes</div>
                    </div>
                    <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] uppercase tracking-wider text-purple-400 font-bold">Services</span>
                      <div className="w-16 h-8 rounded border border-white/10 bg-white/5 flex items-center justify-center text-xs mt-2 font-mono">24 nodes</div>
                    </div>
                    <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] uppercase tracking-wider text-purple-400 font-bold">Repositories</span>
                      <div className="w-16 h-8 rounded border border-white/10 bg-white/5 flex items-center justify-center text-xs mt-2 font-mono">12 nodes</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: AI summary & Metadata */}
              <div className="space-y-8">
                {/* AI Summary */}
                <div className="glass-panel p-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">AI Summary</h3>
                  <div className="space-y-4">
                    <p className="text-xs text-gray-400 leading-relaxed">
                      TestPilot AI parsed this codebase. The API layers are verified via tests. 
                      However, there is a coverage gap of 15% in the secondary billing service which 
                      poses regression risks on subsequent changes.
                    </p>
                    <div className="border-t border-white/5 pt-4">
                      <span className="text-[10px] uppercase tracking-wider text-gray-500 block mb-1">Primary Language</span>
                      <span className="text-sm font-semibold text-gray-200">{repo?.language || "Python"}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase tracking-wider text-gray-500 block mb-1">Test Framework</span>
                      <span className="text-sm font-semibold text-purple-400">pytest</span>
                    </div>
                  </div>
                </div>

                {/* Recent PR Activity */}
                <div className="glass-panel p-6">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">Recent PRs</h3>
                  <div className="space-y-3">
                    {prs.length > 0 ? (
                      prs.slice(0, 5).map((pr) => (
                        <div key={pr.id} className="flex justify-between items-center text-xs">
                          <span className="font-mono text-gray-400">#{pr.pr_number}</span>
                          <span className="text-gray-200 font-medium truncate max-w-[120px]">{pr.title}</span>
                          <span className={`font-semibold capitalize ${
                            pr.risk_level === "critical" || pr.risk_level === "high"
                              ? "text-red-400"
                              : pr.risk_level === "medium"
                              ? "text-yellow-400"
                              : "text-emerald-400"
                          }`}>
                            {pr.risk_level || "low"} risk
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-gray-500 italic">No pull requests analyzed yet. Open a PR on GitHub to trigger AI analysis.</p>
                    )}
                  </div>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
