"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Sidebar from "@/components/Sidebar";
import { repositoriesApi, Repository } from "@/lib/api/repositories";

export default function Repositories() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [fullName, setFullName] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const res = await repositoriesApi.list().catch(() => null);
        if (res && res.items) {
          setRepos(res.items);
        } else {
          throw new Error("Backend offline - using mock repositories");
        }
      } catch {
        // Fallback mock repositories for preview mode
        setRepos([
          {
            id: "repo-1",
            full_name: "modern-corp/payment-gateway",
            name: "payment-gateway",
            owner_login: "modern-corp",
            description: "Core async payment integration endpoints and ledger billing engines.",
            clone_url: "https://github.com/modern-corp/payment-gateway.git",
            default_branch: "main",
            language: "Python",
            is_private: true,
            is_indexed: true,
            indexed_at: new Date().toISOString(),
            index_status: "indexed",
            total_files: 142,
            total_functions: 1042,
            total_classes: 248,
            health_score: 92.5,
            coverage_percentage: 84.6,
            created_at: new Date().toISOString(),
          },
          {
            id: "repo-2",
            full_name: "modern-corp/user-auth-service",
            name: "user-auth-service",
            owner_login: "modern-corp",
            description: "Distributed JWT authorization scopes and secure session validations.",
            clone_url: "https://github.com/modern-corp/user-auth-service.git",
            default_branch: "main",
            language: "Go",
            is_private: true,
            is_indexed: true,
            indexed_at: new Date().toISOString(),
            index_status: "indexed",
            total_files: 45,
            total_functions: 310,
            total_classes: 15,
            health_score: 88.0,
            coverage_percentage: 72.8,
            created_at: new Date().toISOString(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    let repoName = fullName.trim();
    if (repoName && !repoName.includes("/")) {
      repoName = `Shikhaar/${repoName}`;
    }

    setConnecting(true);
    setError("");
    try {
      const res = await repositoriesApi.connect(repoName);
      setRepos((prev) => [res.data, ...prev]);
      setFullName("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to connect repository");
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#030303]">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto px-10 py-8">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Connected Repositories</h1>
            <p className="text-gray-500 text-sm">Manage connected codebases and trigger indices</p>
          </div>
        </header>

        {/* Connect Repo Form */}
        <section className="glass-panel p-6 mb-8">
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">Connect new repository</h2>
          <form onSubmit={handleConnect} className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. owner/repository"
                className="w-full px-4 py-2.5 glass-input text-sm"
                required
              />
            </div>
            <button
              type="submit"
              disabled={connecting}
              className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 text-white rounded-lg text-sm font-semibold transition"
            >
              {connecting ? "Connecting..." : "Connect"}
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
                  <p className="text-gray-400 text-xs line-clamp-2 mb-4">{repo.description || "No description provided."}</p>
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
