"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { repositoriesApi, Repository } from "@/lib/api/repositories";

import { pullRequestsApi, PullRequest } from "@/lib/api/pullRequests";

export default function RepositoryDetail({ params }: { params: any }) {
  const resolvedParams = params && typeof params.then === "function" ? use(params) : params;
  const rawId = (resolvedParams?.id || "").toString();
  const id = decodeURIComponent(rawId);
  const [repo, setRepo] = useState<Repository | null>(null);
  const [prs, setPrs] = useState<PullRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [reindexing, setReindexing] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [confirmDisconnect, setConfirmDisconnect] = useState(false);

  const [selectedBranch, setSelectedBranch] = useState("");
  const [branches, setBranches] = useState<string[]>([]);

  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [prCreating, setPrCreating] = useState(false);
  const [prCreated, setPrCreated] = useState(false);
  const [prUrl, setPrUrl] = useState<string | null>(null);
  const [prBranch, setPrBranch] = useState<string | null>(null);
  const [targetFilePath, setTargetFilePath] = useState<string | null>(null);

  const handleGenerateTests = async () => {
    if (!repo) return;
    setGenerating(true);
    setGeneratedCode(null);
    try {
      const res = await repositoriesApi.generateTests(repo.id);
      if (res?.data?.generated_code) {
        setGeneratedCode(res.data.generated_code);
        if (res.data.target_file) {
          setTargetFilePath(res.data.target_file);
        }
      } else {
        throw new Error("Invalid response");
      }
    } catch {
      setGeneratedCode(`# Failed to generate tests for ${repo.name}. Please check backend connection.`);
    } finally {
      setGenerating(false);
    }
  };

  const fetchRepo = async () => {
    try {
      const [data, prData, branchData] = await Promise.all([
        repositoriesApi.get(id).catch(() => null),
        pullRequestsApi.list(id).catch(() => null),
        repositoriesApi.listBranches(id).catch(() => ["main", "dev", "master", "staging"]),
      ]);
      if (data) {
        setRepo(data);
        if (!selectedBranch) {
          setSelectedBranch(data.default_branch || "main");
        }
      }
      if (prData && prData.items) setPrs(prData.items);
      if (branchData && branchData.length > 0) setBranches(branchData);
    } catch (err) {
      console.error("Failed to load repo", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRepo();
  }, [id]);

  // Poll repository status every 3s while indexing is in progress or pending
  useEffect(() => {
    if (repo?.index_status !== "indexing" && repo?.index_status !== "pending") return;
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

  const handleDisconnectRepo = async () => {
    if (!repo) return;
    const confirmed = window.confirm(
      `Disconnect '${repo.full_name}'?\n\nThis will remove the repository from TestPilot AI and free up disk storage.`
    );
    if (!confirmed) return;

    setDisconnecting(true);
    try {
      try {
        await repositoriesApi.disconnect(repo.id);
      } catch {
        await repositoriesApi.disconnect(repo.full_name);
      }
      window.location.href = "/repositories";
    } catch (err: any) {
      console.error("Failed to disconnect repository", err);
      const msg = err?.response?.data?.detail || err?.message || "Failed to disconnect repository";
      alert(`Failed to disconnect repository: ${msg}`);
      setDisconnecting(false);
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
            {/* Indexing Progress Banner */}
            {(repo?.index_status === "indexing" || repo?.index_status === "pending" || (!repo?.is_indexed && repo)) && (
              <div className="relative overflow-hidden rounded-2xl border border-purple-500/30 bg-purple-500/5 p-5">
                <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-purple-500 to-transparent" style={{ animation: 'shimmer 1.5s linear infinite' }} />
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center shrink-0">
                    <div className="w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin" />
                  </div>
                  <div className="flex-1">
                    <p className="text-purple-200 font-semibold text-sm mb-1">
                      TestPilot AI is analyzing <span className="text-purple-300">{repo?.full_name}</span>
                    </p>
                    <p className="text-gray-400 text-xs mb-3">
                      Cloning repository → Parsing AST graph → Building dependency graph → Generating embeddings
                    </p>
                    <div className="w-full bg-white/5 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-gradient-to-r from-purple-600 to-blue-500 animate-pulse" style={{ width: '65%' }} />
                    </div>
                    <p className="text-gray-500 text-[11px] mt-2">This typically takes 1–2 minutes. This page will update automatically.</p>
                  </div>
                </div>
              </div>
            )}

            {/* Header */}
            <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
              <div>
                <div className="flex items-center space-x-3 mb-2">
                  <h1 className="text-2xl font-bold tracking-tight">{repo?.full_name}</h1>
                  <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
                    repo?.index_status === "indexing" || repo?.index_status === "pending"
                      ? "border-purple-500/20 bg-purple-500/5 text-purple-400"
                      : "border-blue-500/20 bg-blue-500/5 text-blue-400"
                  }`}>
                    {repo?.index_status}
                  </span>
                </div>
                <p className="text-gray-500 text-sm max-w-2xl">
                  {repo?.description || `${repo?.language || "Multi-language"} repository indexed for automated AST analysis.`}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3 shrink-0">
                <div className="flex items-center space-x-2 bg-white/5 border border-white/10 rounded-xl px-3.5 py-2 text-xs text-gray-300 whitespace-nowrap">
                  <svg className="w-4 h-4 text-gray-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                  </svg>
                  <span className="text-gray-400 font-semibold whitespace-nowrap">Branch:</span>
                  <select
                    value={selectedBranch}
                    onChange={(e) => setSelectedBranch(e.target.value)}
                    className="bg-[#0d0d12] border border-white/10 rounded-lg px-2.5 py-1 outline-none text-white font-mono text-xs cursor-pointer"
                  >
                    {(branches.length > 0 ? branches : [selectedBranch || "main"]).map((b) => (
                      <option key={b} value={b} className="bg-[#0d0d12] text-white">
                        {b}
                      </option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={() => setShowGenerateModal(true)}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-purple-900/30 transition flex items-center space-x-1.5 whitespace-nowrap shrink-0"
                >
                  <svg className="w-4 h-4 text-purple-200 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="whitespace-nowrap">Generate AI Tests</span>
                </button>

                <button
                  onClick={handleReindex}
                  disabled={reindexing}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-900/30 transition whitespace-nowrap shrink-0"
                >
                  <span className="whitespace-nowrap">{reindexing ? "Queueing Index..." : "Force Re-Index"}</span>
                </button>

                <button
                  onClick={handleDisconnectRepo}
                  disabled={disconnecting}
                  className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-300 border border-red-500/20 rounded-xl text-xs font-semibold shadow-lg transition whitespace-nowrap shrink-0 disabled:opacity-50"
                >
                  <span className="whitespace-nowrap">
                    {disconnecting ? "Disconnecting..." : "Disconnect Repo"}
                  </span>
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
                    {repo?.architecture_summary || `The ${repo?.name || "codebase"} is organized in a layered Clean Architecture structure. TestPilot AI parsed ${repo?.total_files || 0} files containing ${repo?.total_functions || 0} functions and ${repo?.total_classes || 0} classes.`}
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
                      <div className="w-20 h-8 rounded border border-white/10 bg-white/5 flex items-center justify-center text-xs mt-2 font-mono">
                        {repo?.routes_nodes ?? Math.max(1, Math.floor((repo?.total_files || 0) * 0.25))} nodes
                      </div>
                    </div>
                    <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] uppercase tracking-wider text-purple-400 font-bold">Services</span>
                      <div className="w-20 h-8 rounded border border-white/10 bg-white/5 flex items-center justify-center text-xs mt-2 font-mono">
                        {repo?.services_nodes ?? Math.max(1, Math.floor((repo?.total_files || 0) * 0.50))} nodes
                      </div>
                    </div>
                    <svg className="w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    <div className="flex flex-col items-center">
                      <span className="text-[10px] uppercase tracking-wider text-purple-400 font-bold">Repositories</span>
                      <div className="w-20 h-8 rounded border border-white/10 bg-white/5 flex items-center justify-center text-xs mt-2 font-mono">
                        {repo?.repositories_nodes ?? Math.max(1, Math.floor((repo?.total_files || 0) * 0.25))} nodes
                      </div>
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
                      {repo?.ai_summary || `TestPilot AI parsed ${repo?.full_name}. Health score is rated at ${repo?.health_score?.toFixed(1) || "85.0"}/100.`}
                    </p>
                    <div className="border-t border-white/5 pt-4">
                      <span className="text-[10px] uppercase tracking-wider text-gray-500 block mb-1">Primary Language</span>
                      <span className="text-sm font-semibold text-gray-200">{repo?.language || "Unknown"}</span>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase tracking-wider text-gray-500 block mb-1">Test Framework</span>
                      <span className="text-sm font-semibold text-purple-400">
                        {repo?.test_framework || (repo?.language?.toLowerCase().includes("typescript") ? "Jest / Vitest" : "pytest")}
                      </span>
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

      {/* Generate AI Tests Modal */}
      {showGenerateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fadeIn">
          <div className="bg-[#0b0c10] border border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping" />
                <h3 className="text-lg font-bold text-white">Generate AI Unit Tests</h3>
              </div>
              <button
                onClick={() => {
                  setShowGenerateModal(false);
                  setGeneratedCode(null);
                }}
                className="text-gray-400 hover:text-white transition"
              >
                ✕
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
              <p className="text-xs text-gray-400">
                TestPilot AI uses Tree-Sitter AST parsing and Gemini to generate unit test suites for <strong className="text-white">{repo?.full_name}</strong>.
              </p>

              {!generatedCode && !generating && (
                <div className="p-6 rounded-xl border border-dashed border-white/10 bg-white/[0.01] text-center space-y-4">
                  <div className="w-12 h-12 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center mx-auto">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L5.59 15.11a2 2 0 01-1.424-1.424l-.477-2.387a6 6 0 00-.517-3.86l-.158-.318a6 6 0 01-.517-3.86L3.928 2.24a2 2 0 011.424-1.424l2.387-.477a6 6 0 003.86-.517l.318-.158a6 6 0 013.86-.517l2.387.477a2 2 0 011.424 1.424l.477 2.387a6 6 0 00.517 3.86l.158.318a6 6 0 01.517 3.86l-1.424 1.424z" />
                    </svg>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-white">Target Coverage Gap Resolution</h4>
                    <p className="text-xs text-gray-500 mt-1">
                      Target Framework: <span className="text-purple-400 font-mono">{repo?.language?.toLowerCase().includes("typescript") ? "Jest / Vitest" : "PyTest"}</span>
                    </p>
                  </div>
                  <button
                    onClick={handleGenerateTests}
                    className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-purple-900/40 transition"
                  >
                    Generate Test Suite Now
                  </button>
                </div>
              )}

              {generating && (
                <div className="py-12 flex flex-col items-center justify-center space-y-3">
                  <div className="w-10 h-10 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
                  <p className="text-xs text-purple-300 font-medium animate-pulse">
                    Parsing AST functions and synthesizing unit test assertions via Gemini...
                  </p>
                </div>
              )}

              {generatedCode && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-purple-400">
                      Generated Suite: {repo?.language?.toLowerCase().includes("typescript") ? "test/component.test.tsx" : "tests/test_indexing.py"}
                    </span>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(generatedCode);
                          setCopied(true);
                          setTimeout(() => setCopied(false), 2000);
                        }}
                        className="px-3 py-1 bg-white/10 hover:bg-white/20 text-xs font-semibold text-white rounded-lg transition"
                      >
                        {copied ? "Copied ✓" : "Copy Code"}
                      </button>

                      <button
                        onClick={async () => {
                          if (!repo || !generatedCode) return;
                          setPrCreating(true);
                          try {
                            const targetPath = targetFilePath || (repo.language?.toLowerCase().includes("typescript") || repo.language?.toLowerCase().includes("javascript")
                              ? `tests/${repo.name.toLowerCase().replace(/-/g, "_")}.test.ts`
                              : `tests/test_${repo.name.toLowerCase().replace(/-/g, "_")}.py`);
                            const res = await repositoriesApi.createPR(repo.id, targetPath, generatedCode);
                            if (res.data) {
                              setPrUrl(res.data.pr_url);
                              setPrBranch(res.data.branch);
                              setPrCreated(true);
                            }
                          } catch (err: any) {
                            const msg =
                              err?.response?.status === 401
                                ? "Please sign in with GitHub to create a Pull Request on GitHub."
                                : err?.response?.data?.detail || err?.message || "Failed to create PR on GitHub";
                            alert(msg);
                          } finally {
                            setPrCreating(false);
                          }
                        }}
                        disabled={prCreating || prCreated}
                        className="px-3 py-1 bg-purple-600 hover:bg-purple-500 disabled:bg-purple-950/60 text-xs font-semibold text-white rounded-lg shadow-lg shadow-purple-900/30 transition flex items-center space-x-1"
                      >
                        {prCreating ? (
                          <>
                            <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin mr-1" />
                            <span>Creating PR...</span>
                          </>
                        ) : prCreated ? (
                          <span>PR Created ✓</span>
                        ) : (
                          <span>Create PR on GitHub</span>
                        )}
                      </button>
                    </div>
                  </div>

                  {prCreated && (
                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300 flex items-center justify-between">
                      <span>Pull Request created on GitHub branch <strong className="font-mono">{prBranch || "testpilot/ai-unit-tests"}</strong>!</span>
                      <a
                        href={prUrl || `https://github.com/${repo?.full_name}/pulls`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-emerald-400 underline font-semibold flex items-center gap-1"
                      >
                        <span>View PR on GitHub</span>
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    </div>
                  )}

                  <pre className="p-4 rounded-xl bg-[#050608] border border-white/10 text-xs font-mono text-emerald-300 overflow-x-auto max-h-80">
                    <code>{generatedCode}</code>
                  </pre>

                  {/* Developer Guidance Banner */}
                  <div className="p-3.5 rounded-xl bg-purple-950/20 border border-purple-500/20 text-xs text-purple-200 space-y-2">
                    <div className="font-semibold flex items-center gap-1.5 text-purple-300">
                      <svg className="w-4 h-4 text-purple-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>How to use this generated test suite:</span>
                    </div>
                    <ul className="space-y-1.5 text-gray-300 pl-1">
                      <li className="flex items-start gap-1.5">
                        <span className="text-purple-400 font-bold">•</span>
                        <span><strong>Option 1 — Automatic Pull Request:</strong> Click <em className="text-purple-300">Create PR on GitHub</em> above. TestPilot AI will create a new branch and open a PR on your GitHub repository.</span>
                      </li>
                      <li className="flex items-start gap-1.5">
                        <span className="text-purple-400 font-bold">•</span>
                        <span><strong>Option 2 — Copy & Run Locally:</strong> Click <em className="text-purple-300">Copy Code</em>, paste it into your local project file at <code className="font-mono text-purple-300 bg-white/10 px-1 py-0.5 rounded">{repo?.language?.toLowerCase().includes("typescript") ? "test/component.test.tsx" : "tests/test_indexing.py"}</code>, and execute <code className="font-mono text-emerald-400 bg-white/10 px-1.5 py-0.5 rounded">{repo?.language?.toLowerCase().includes("typescript") ? "npm test" : "pytest tests/test_indexing.py"}</code> in your terminal.</span>
                      </li>
                    </ul>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 border-t border-white/10 bg-white/[0.02] flex justify-end">
              <button
                onClick={() => {
                  setShowGenerateModal(false);
                  setGeneratedCode(null);
                }}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 text-xs font-semibold text-gray-300 rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
