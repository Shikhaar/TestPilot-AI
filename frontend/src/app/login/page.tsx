"use client";

import { useState } from "react";
import { authApi } from "@/lib/api/auth";

export default function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGitHubLogin = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await authApi.getLoginUrl().catch(() => null);
      if (data && data.url) {
        // Redirect browser to GitHub OAuth authorize page
        window.location.href = data.url;
      } else {
        throw new Error("Backend offline");
      }
    } catch {
      setError("Backend API is currently offline (http://localhost:8000). Start FastAPI backend to enable GitHub OAuth.");
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#030303] px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 glass-panel p-8 text-center relative overflow-hidden">
        {/* Decorative glows */}
        <div className="absolute top-[-50%] left-[-50%] w-[100%] h-[100%] rounded-full bg-purple-900/10 blur-[80px] pointer-events-none" />
        
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-gray-100">Sign in to TestPilot AI</h2>
          <p className="text-sm text-gray-500">AI-Powered Regression Testing Platform</p>
        </div>

        <div className="mt-8 space-y-4">
          <button
            onClick={handleGitHubLogin}
            disabled={loading}
            className="w-full flex justify-center items-center gap-3 px-4 py-3 bg-white text-black font-semibold rounded-lg hover:bg-gray-100 disabled:bg-gray-300 transition"
          >
            {/* GitHub custom SVG logo */}
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
            </svg>
            <span>{loading ? "Connecting..." : "Continue with GitHub"}</span>
          </button>

          {error && <p className="text-red-400 text-xs mt-2">{error}</p>}
        </div>
      </div>
    </div>
  );
}
