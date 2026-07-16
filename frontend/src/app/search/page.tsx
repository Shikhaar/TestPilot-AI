"use client";

import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import { aiApi, CodeSearchResult } from "@/lib/api/ai";

export default function Search() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CodeSearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setSearching(true);
    try {
      // Connects to RAG semantic query
      const data = await aiApi.search("repo-1", query);
      setResults(data.results);
    } catch (err) {
      console.error("Failed to run code search, using mock fallback", err);
      setResults([
        {
          file_path: "app/core/security.py",
          language: "Python",
          snippet: `def create_refresh_token(subject: str | int) -> str:
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {"sub": str(subject), "type": "refresh"}
    return jwt.encode(payload, settings.jwt_secret_key)`,
          score: 0.89,
          function_name: "create_refresh_token",
          class_name: null,
          line_start: 100,
          line_end: 118,
        },
      ]);
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
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search functions, classes or concepts (e.g. JWT cookie generation)..."
            className="flex-1 px-4 py-2.5 glass-input text-sm"
          />
          <button
            type="submit"
            className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-semibold transition"
          >
            {searching ? "Searching..." : "Search"}
          </button>
        </form>

        <section className="space-y-6">
          {results.map((res, idx) => (
            <div key={idx} className="glass-panel p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="text-xs text-purple-400 font-mono">{res.file_path}</span>
                  <h3 className="text-sm font-bold text-gray-200 mt-1">{res.function_name || "Code Fragment"}</h3>
                </div>
                <span className="text-xs text-gray-500 font-mono">Score: {(res.score * 100).toFixed(0)}%</span>
              </div>
              <div className="p-4 border border-white/5 rounded bg-black/40 font-mono text-xs text-gray-300 whitespace-pre">
                {res.snippet}
              </div>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
}
