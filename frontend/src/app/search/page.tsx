"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { aiApi, CodeSearchResult } from "@/lib/api/ai";
import { repositoriesApi, Repository } from "@/lib/api/repositories";

export default function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CodeSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepoId, setSelectedRepoId] = useState<string>("");
  const [loadingRepos, setLoadingRepos] = useState(true);

  useEffect(() => {
    async function loadRepos() {
      try {
        const data = await repositoriesApi.list();
        const repos = data.items || [];
        setRepositories(repos);
        if (repos.length > 0) {
          setSelectedRepoId(repos[0].id);
        }
      } catch (err) {
        console.error("Failed to load repositories for search", err);
      } finally {
        setLoadingRepos(false);
      }
    }
    loadRepos();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query || !selectedRepoId) return;

    setSearching(true);
    try {
      // Query selected repository via Qdrant semantic search engine
      const data = await aiApi.search(selectedRepoId, query);
      setResults(data.results || []);
    } catch (err) {
      console.error("Failed to run code search", err);
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#030303]">
      <Sidebar />
      
      <main className="flex-1 overflow-y-auto px-10 py-8">
        <header className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight">Code Search</h1>
          <p className="text-gray-500 text-sm">Semantic and structural code query engine powered by Qdrant</p>
        </header>

        <form onSubmit={handleSearch} className="flex gap-4 mb-8">
          {/* Repository Selector Dropdown */}
          <select
            value={selectedRepoId}
            onChange={(e) => setSelectedRepoId(e.target.value)}
            disabled={loadingRepos || repositories.length === 0}
            className="px-4 py-2.5 glass-input text-sm bg-black/60 text-gray-200 border border-white/10 rounded-lg outline-none focus:border-purple-500 max-w-xs cursor-pointer"
          >
            {loadingRepos ? (
              <option value="">Loading repositories...</option>
            ) : repositories.length === 0 ? (
              <option value="">No repositories connected</option>
            ) : (
              repositories.map((repo) => (
                <option key={repo.id} value={repo.id} className="bg-gray-900 text-gray-200">
                  {repo.full_name} {repo.is_indexed ? "✓" : "(Not Indexed)"}
                </option>
              ))
            )}
          </select>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search functions, classes or concepts (e.g. JWT cookie generation)..."
            className="flex-1 px-4 py-2.5 glass-input text-sm"
          />
          <button
            type="submit"
            disabled={searching || !selectedRepoId}
            className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-sm font-semibold transition"
          >
            {searching ? "Searching..." : "Search"}
          </button>
        </form>

        <section className="space-y-6">
          {results.length === 0 && !searching && (
            <div className="glass-panel p-8 text-center text-gray-500 text-sm">
              {repositories.length === 0
                ? "Connect a repository first to start searching code."
                : "Type a query and hit Search to view semantic code results."}
            </div>
          )}

          {results.map((res, idx) => (
            <div key={idx} className="glass-panel p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="text-xs text-purple-400 font-mono">{res.file_path}</span>
                  <h3 className="text-sm font-bold text-gray-200 mt-1">{res.function_name || "Code Fragment"}</h3>
                </div>
                <span className="text-xs text-gray-500 font-mono">Score: {(res.score * 100).toFixed(0)}%</span>
              </div>
              <div className="p-4 border border-white/5 rounded bg-black/40 font-mono text-xs text-gray-300 whitespace-pre overflow-x-auto">
                {res.snippet}
              </div>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
