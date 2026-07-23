"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { repositoriesApi, Repository } from "@/lib/api/repositories";

const DEFAULT_USER_REPOS = [
  { full_name: "Shikhaar/TestPilot-AI", name: "TestPilot-AI" },
  { full_name: "Shikhaar/Portfolio2.0", name: "Portfolio2.0" },
  { full_name: "Shikhaar/Portfolio", name: "Portfolio" },
  { full_name: "Shikhaar/Idea", name: "Idea" },
  { full_name: "Shikhaar/passop", name: "passop" },
];

export default function Repositories() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [userGitHubRepos, setUserGitHubRepos] = useState<Array<{ full_name: string; name: string }>>(DEFAULT_USER_REPOS);
  const [loading, setLoading] = useState(true);
  const [selectedRepo, setSelectedRepo] = useState("");
  const [customRepo, setCustomRepo] = useState("");
  const [isCustom, setIsCustom] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const [res, ghRepos] = await Promise.all([
          repositoriesApi.list().catch(() => null),
          repositoriesApi.listUserGitHubRepos().catch(() => []),
        ]);
        if (res && res.items) {
          setRepos(res.items);
        }
        if (ghRepos && ghRepos.length > 0) {
          const top5 = ghRepos.slice(0, 5);
          setUserGitHubRepos(top5);
        }
      } catch (e) {
        console.error("Failed to load repositories data", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    let targetRepo = isCustom ? customRepo.trim() : selectedRepo;
    if (!targetRepo) {
      setError("Please select a repository from the list or enter a custom repository name.");
      return;
    }

    // Support full GitHub URL parsing (e.g. https://github.com/Shikhaar/DSA.git -> Shikhaar/DSA)
    if (targetRepo.includes("github.com/")) {
      const parts = targetRepo.split("github.com/")[1].replace(/\.git$/, "").split("/");
      if (parts.length >= 2) {
        targetRepo = `${parts[0]}/${parts[1]}`;
      }
    }

    setConnecting(true);
    setError("");

    try {
      const newRepo = await repositoriesApi.connect(targetRepo);
      setRepos([newRepo.data, ...repos]);
      setCustomRepo("");
      setSelectedRepo("");
      setIsCustom(false);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.message || err.message || "Failed to connect repository";
      setError(msg);
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#030303]">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto px-10 py-8">
        {/* Header */}
        <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Connected Repositories</h1>
            <p className="text-gray-500 text-sm">Manage connected codebases, index AST structures, and run test suites</p>
          </div>

          <a
            href="https://github.com/apps/testpilot-ai-shikhar/installations/new"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-purple-900/30 transition flex items-center space-x-2 border border-white/10"
          >
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
            <span>Install TestPilot AI GitHub App ↗</span>
          </a>
        </header>

        {/* Connect Repo Form */}
        <section className="glass-panel p-6 mb-8">
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">Connect new repository</h2>
          <form onSubmit={handleConnect} className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
            <div className="flex-1">
              {!isCustom ? (
                <select
                  value={selectedRepo}
                  onChange={(e) => {
                    if (e.target.value === "custom") {
                      setIsCustom(true);
                    } else {
                      setSelectedRepo(e.target.value);
                    }
                  }}
                  className="w-full px-4 py-2.5 glass-input text-sm bg-[#0d0d12] text-white border border-white/10 rounded-lg outline-none cursor-pointer"
                >
                  <option value="" disabled hidden className="bg-[#0d0d12] text-gray-500">
                    Select a repository...
                  </option>
                  {userGitHubRepos.slice(0, 5).map((r) => (
                    <option key={r.full_name} value={r.full_name} className="bg-[#0d0d12] text-white">
                      {r.full_name}
                    </option>
                  ))}
                  <option value="custom" className="bg-[#0d0d12] text-purple-400 font-semibold">
                    + Enter Custom Repository Name or URL...
                  </option>
                </select>
              ) : (
                <div className="space-y-1">
                  <div className="flex justify-between items-center text-xs mb-1">
                    <span className="text-gray-400">Custom Repo Name or URL</span>
                    <button
                      type="button"
                      onClick={() => setIsCustom(false)}
                      className="text-purple-400 hover:text-purple-300 font-medium"
                    >
                      ← Back to Repositories Dropdown
                    </button>
                  </div>
                  <input
                    type="text"
                    value={customRepo}
                    onChange={(e) => setCustomRepo(e.target.value)}
                    placeholder="e.g. Shikhaar/DSA or https://github.com/Shikhaar/DSA"
                    className="w-full px-4 py-2.5 glass-input text-sm text-white"
                    autoFocus
                    required
                  />
                </div>
              )}
            </div>
            <button
              type="submit"
              disabled={connecting}
              className="px-6 py-2.5 bg-blue-700 hover:bg-blue-800 disabled:bg-gray-800 text-white rounded-lg text-sm font-semibold shadow-lg shadow-blue-900/30 transition self-start sm:self-auto"
            >
              {connecting ? "Connecting..." : "Connect Repository"}
            </button>
          </form>
          {error && <p className="text-red-400 text-xs mt-2">{error}</p>}
        </section>

        {/* Repositories List */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {repos.map((repo) => (
              <div key={repo.id} className="glass-card p-6 flex flex-col justify-between h-56">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-base font-bold text-gray-100 hover:text-purple-400 transition">
                      <Link href={`/repositories/${repo.id}`}>{repo.full_name}</Link>
                    </h3>
                    <span className={`text-[10px] px-2 py-0.5 rounded border ${
                      repo.is_private
                        ? "text-orange-400 border-orange-500/20 bg-orange-500/5"
                        : "text-green-400 border-green-500/20 bg-green-500/5"
                    }`}>
                      {repo.is_private ? "Private" : "Public"}
                    </span>
                  </div>
                  <p className="text-gray-400 text-xs line-clamp-2 mb-4">
                    {repo.description || (
                      repo.full_name.toLowerCase().includes("testpilot")
                        ? "AI-powered test generation, AST parsing, and PR risk analysis platform for multi-language codebases."
                        : repo.full_name.toLowerCase().includes("portfolio")
                        ? "Modern portfolio web application showcasing AI projects, full-stack systems, and interactive UI design."
                        : `Automated test generation and AST code indexing for ${repo.name}.`
                    )}
                  </p>
                </div>

                <div className="border-t border-white/5 pt-4 flex justify-between items-center text-xs text-gray-500">
                  <div className="flex space-x-4">
                    <span>Lang: <strong className="text-gray-300">{repo.language || "Unknown"}</strong></span>
                    <span>Health: <strong className="text-purple-400">{repo.health_score ? repo.health_score.toFixed(1) : "N/A"}</strong></span>
                    <span>Cov: <strong className="text-gray-300">{repo.coverage_percentage ? `${repo.coverage_percentage}%` : "N/A"}</strong></span>
                  </div>
                  <Link
                    href={`/repositories/${repo.id}`}
                    className="text-purple-400 hover:text-purple-300 font-semibold"
                  >
                    View Details →
                  </Link>
                </div>
              </div>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}
