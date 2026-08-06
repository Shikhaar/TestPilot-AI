"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { repositoriesApi, Repository } from "@/lib/api/repositories";

export default function Repositories() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [userGitHubRepos, setUserGitHubRepos] = useState<Array<{ full_name: string; name: string }>>([]);
  const [ghReposError, setGhReposError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [vcsProvider, setVcsProvider] = useState<"github" | "bitbucket" | "gitlab" | "custom_git">("github");
  const [accessToken, setAccessToken] = useState("");
  const [selectedRepo, setSelectedRepo] = useState("");
  const [customRepo, setCustomRepo] = useState("");
  const [isCustom, setIsCustom] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");
  const [disconnectingId, setDisconnectingId] = useState<string | null>(null);
  const [disconnectConfirmId, setDisconnectConfirmId] = useState<string | null>(null);

  const handleDisconnect = async (repo: Repository, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const confirmed = window.confirm(
      `Disconnect '${repo.full_name}'?\n\nThis will remove the repository from TestPilot AI and free up disk storage.`
    );
    if (!confirmed) return;

    setDisconnectingId(repo.id);
    setError("");
    try {
      try {
        await repositoriesApi.disconnect(repo.id);
      } catch {
        await repositoriesApi.disconnect(repo.full_name);
      }
      setRepos((prev) => prev.filter((r) => r.id !== repo.id && r.full_name !== repo.full_name));
    } catch (err: any) {
      console.error("Disconnect error:", err);
      const msg = err?.response?.data?.detail || err?.message || "Failed to disconnect repository";
      setError(msg);
      alert(`Failed to disconnect repository: ${msg}`);
    } finally {
      setDisconnectingId(null);
    }
  };

  const isIndexing = (repo: Repository) =>
    repo.index_status === "indexing" || repo.index_status === "pending" || !repo.is_indexed;

  const fetchRepos = async () => {
    try {
      const res = await repositoriesApi.list().catch(() => null);
      if (res && res.items) setRepos(res.items);
    } catch (e) {
      console.error("Failed to refresh repositories", e);
    }
  };

  useEffect(() => {
    async function loadData() {
      try {
        const [res, ghRepos] = await Promise.all([
          repositoriesApi.list().catch(() => null),
          repositoriesApi.listUserGitHubRepos().catch(() => null),
        ]);
        if (res && res.items) {
          setRepos(res.items);
        }
        if (ghRepos && ghRepos.length > 0) {
          setUserGitHubRepos(ghRepos.slice(0, 10));
        } else if (ghRepos === null) {
          setGhReposError(true);
        }
      } catch (e) {
        console.error("Failed to load repositories data", e);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Auto-poll every 5 seconds while any repo is still indexing
  useEffect(() => {
    const hasIndexing = repos.some(isIndexing);
    if (!hasIndexing) return;
    const interval = setInterval(fetchRepos, 5000);
    return () => clearInterval(interval);
  }, [repos]);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    let targetRepo = isCustom || vcsProvider !== "github" ? customRepo.trim() : selectedRepo;
    if (!targetRepo) {
      setError("Please enter or select a repository name/URL.");
      return;
    }

    // Support full Git URL parsing
    if (targetRepo.includes("github.com/")) {
      const parts = targetRepo.split("github.com/")[1].replace(/\.git$/, "").split("/");
      if (parts.length >= 2) {
        targetRepo = `${parts[0]}/${parts[1]}`;
      }
    } else if (targetRepo.includes("bitbucket.org/")) {
      const parts = targetRepo.split("bitbucket.org/")[1].replace(/\.git$/, "").split("/");
      if (parts.length >= 2) {
        targetRepo = `${parts[0]}/${parts[1]}`;
      }
    } else if (targetRepo.includes("gitlab.com/")) {
      const parts = targetRepo.split("gitlab.com/")[1].replace(/\.git$/, "").split("/");
      if (parts.length >= 2) {
        targetRepo = `${parts[0]}/${parts[1]}`;
      }
    }

    setConnecting(true);
    setError("");

    try {
      const newRepo = await repositoriesApi.connect(targetRepo, vcsProvider, accessToken);
      setRepos([newRepo.data, ...repos]);
      setCustomRepo("");
      setSelectedRepo("");
      setAccessToken("");
      setIsCustom(false);
    } catch (err: any) {
      const msg =
        err?.response?.status === 401
          ? "Please sign in or provide a valid access token."
          : err?.response?.data?.detail || err?.response?.data?.message || err.message || "Failed to connect repository";
      setError(msg);
    } finally {
      setConnecting(false);
    }
  };

  const getPlaceholder = () => {
    switch (vcsProvider) {
      case "bitbucket":
        return "e.g. workspace/repo-name or https://bitbucket.org/workspace/repo-name";
      case "gitlab":
        return "e.g. group/project-name or https://gitlab.com/group/project-name";
      case "custom_git":
        return "e.g. https://git.company.com/team/service.git";
      default:
        return "e.g. owner/my-repo or https://github.com/owner/my-repo";
    }
  };

  return (
    <div className="flex h-screen bg-[#07090e] font-sans overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-8 text-gray-200">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">Repositories</h1>
            <p className="text-sm text-gray-400 mt-1">Connect, index, and manage VCS repositories across GitHub, Bitbucket, and GitLab.</p>
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
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">Connect VCS repository</h2>
          
          {/* Provider Selection Tabs */}
          <div className="flex space-x-2 mb-4 border-b border-gray-800/80 pb-3">
            {[
              { id: "github", label: "GitHub" },
              { id: "bitbucket", label: "Bitbucket" },
              { id: "gitlab", label: "GitLab" },
              { id: "custom_git", label: "Custom Git URL" },
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  setVcsProvider(p.id as any);
                  setError("");
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  vcsProvider === p.id
                    ? "bg-purple-600/30 text-purple-300 border border-purple-500/40 shadow-sm"
                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/40"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleConnect} className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
              <div className="flex-1">
                {vcsProvider === "github" && !isCustom ? (
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
                      Select a GitHub repository...
                    </option>
                    {userGitHubRepos.length === 0 && !ghReposError && (
                      <option disabled className="bg-[#0d0d12] text-gray-500">Loading your GitHub repositories…</option>
                    )}
                    {ghReposError && (
                      <option disabled className="bg-[#0d0d12] text-yellow-400">⚠ Sign in with GitHub to load repositories</option>
                    )}
                    {userGitHubRepos.map((r) => (
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
                    {vcsProvider === "github" && isCustom && (
                      <div className="flex justify-between items-center text-xs mb-1">
                        <span className="text-gray-400">GitHub Repository Name or URL</span>
                        <button
                          type="button"
                          onClick={() => setIsCustom(false)}
                          className="text-purple-400 hover:text-purple-300 font-medium"
                        >
                          ← Back to Repositories Dropdown
                        </button>
                      </div>
                    )}
                    <input
                      type="text"
                      value={customRepo}
                      onChange={(e) => setCustomRepo(e.target.value)}
                      placeholder={getPlaceholder()}
                      className="w-full px-4 py-2.5 glass-input text-sm text-white border border-white/10 rounded-lg outline-none"
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
                {connecting ? "Connecting..." : `Connect ${vcsProvider === "custom_git" ? "Git" : vcsProvider.toUpperCase()} Repo`}
              </button>
            </div>

            {/* Optional Personal Access Token / App Password input for Bitbucket/GitLab/Custom */}
            {vcsProvider !== "github" && (
              <div className="pt-2 border-t border-gray-800/50 flex flex-col sm:flex-row gap-3 items-center">
                <input
                  type="password"
                  value={accessToken}
                  onChange={(e) => setAccessToken(e.target.value)}
                  placeholder={`Optional Access Token / App Password for private ${vcsProvider} repo...`}
                  className="w-full sm:w-2/3 px-3.5 py-1.5 glass-input text-xs text-white border border-white/10 rounded-md"
                />
                <span className="text-[11px] text-gray-500">Leave blank for public repositories</span>
              </div>
            )}
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
              <div key={repo.id} className={`glass-card p-6 flex flex-col justify-between h-56 relative overflow-hidden ${
                isIndexing(repo) ? "border border-purple-500/30" : ""
              }`}>
                {/* Indexing shimmer bar */}
                {isIndexing(repo) && (
                  <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-purple-500 to-transparent animate-[shimmer_1.5s_ease-in-out_infinite]" style={{ backgroundSize: '200% 100%', animation: 'shimmer 1.5s linear infinite' }} />
                )}
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-base font-bold text-gray-100 hover:text-purple-400 transition">
                      <Link href={`/repositories/${repo.id}`}>{repo.full_name}</Link>
                    </h3>
                    <div className="flex items-center gap-2">
                      {isIndexing(repo) && (
                        <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded border text-purple-300 border-purple-500/30 bg-purple-500/10">
                          <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
                          Indexing…
                        </span>
                      )}
                      <span className={`text-[10px] px-2 py-0.5 rounded border ${
                        repo.is_private
                          ? "text-orange-400 border-orange-500/20 bg-orange-500/5"
                          : "text-green-400 border-green-500/20 bg-green-500/5"
                      }`}>
                        {repo.is_private ? "Private" : "Public"}
                      </span>
                      <button
                        onClick={(e) => handleDisconnect(repo, e)}
                        disabled={disconnectingId === repo.id}
                        title="Disconnect repository and free storage"
                        className="text-[10px] px-2 py-0.5 rounded border border-white/10 text-gray-400 hover:text-red-400 hover:border-red-500/40 hover:bg-red-500/5 transition font-medium disabled:opacity-50"
                      >
                        {disconnectingId === repo.id ? "Removing..." : "Disconnect"}
                      </button>
                    </div>
                  </div>
                  {isIndexing(repo) ? (
                    <div className="space-y-1.5 mb-4">
                      <p className="text-purple-300/70 text-xs">
                        🔍 TestPilot AI is cloning and parsing this repository's AST graph. This usually takes 1–2 minutes.
                      </p>
                      <div className="w-full bg-white/5 rounded-full h-1">
                        <div className="bg-purple-500 h-1 rounded-full animate-pulse" style={{ width: '60%' }} />
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-400 text-xs line-clamp-2 mb-4">
                      {repo.description || `${repo.language || "Multi-language"} repository indexed for automated AST analysis.`}
                    </p>
                  )}
                </div>

                <div className="border-t border-white/5 pt-4 flex justify-between items-center text-xs text-gray-500">
                  {isIndexing(repo) ? (
                    <span className="text-gray-500 italic">Metrics available after indexing completes…</span>
                  ) : (
                    <div className="flex space-x-4">
                      <span>Lang: <strong className="text-gray-300">{repo.language || "Unknown"}</strong></span>
                      <span>Health: <strong className="text-purple-400">{repo.health_score ? repo.health_score.toFixed(1) : "N/A"}</strong></span>
                      <span>Cov: <strong className="text-gray-300">{repo.coverage_percentage ? `${repo.coverage_percentage}%` : "N/A"}</strong></span>
                    </div>
                  )}
                  <Link
                    href={`/repositories/${repo.id}`}
                    className="text-purple-400 hover:text-purple-300 font-semibold"
                  >
                    {isIndexing(repo) ? "View Progress →" : "View Details →"}
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
