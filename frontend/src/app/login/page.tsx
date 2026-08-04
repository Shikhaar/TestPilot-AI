"use client";

import { useState } from "react";
import Image from "next/image";
import { authApi } from "@/lib/api/auth";
import Logo from "@/components/Logo";

export default function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGitHubLogin = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await authApi.getLoginUrl();
      if (data && data.url) {
        const callbackUrl = `${window.location.origin}/auth/callback`;
        const redirectUrl = data.url.includes("redirect_uri")
          ? data.url
          : `${data.url}&redirect_uri=${encodeURIComponent(callbackUrl)}`;
        window.location.href = redirectUrl;
      } else {
        throw new Error("Invalid OAuth URL response from backend");
      }
    } catch (err: any) {
      console.error("GitHub Login error:", err);
      const msg = err.response?.data?.detail || err.message || "Network error connecting to backend";
      setError(`GitHub OAuth Error: ${msg}`);
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#030303] overflow-hidden px-4 selection:bg-blue-500 selection:text-white">
      {/* Background Image Wallpaper */}
      <div className="absolute inset-0 z-0 opacity-30 mix-blend-luminosity">
        <Image
          src="/images/login_bg.png"
          alt="TestPilot AI Dark Background"
          fill
          priority
          className="object-cover object-center filter contrast-125 brightness-75 scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#030303] via-[#030303]/80 to-[#030303]/50" />
      </div>

      {/* Ambient Gradient Glows */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[150px] pointer-events-none z-0" />
      <div className="absolute bottom-1/3 right-1/3 w-[400px] h-[400px] bg-purple-600/10 rounded-full blur-[130px] pointer-events-none z-0" />

      {/* Glassmorphism Auth Card */}
      <div className="relative z-10 w-full max-w-md p-8 sm:p-10 rounded-3xl bg-zinc-950/70 border border-white/10 shadow-2xl backdrop-blur-2xl text-center space-y-8">
        
        {/* Logo Badge Container & Header */}
        <div className="space-y-4 flex flex-col items-center">
          <div className="p-3.5 bg-gradient-to-b from-blue-500/10 to-indigo-500/5 rounded-2xl border border-blue-500/20 shadow-lg shadow-blue-500/10 inline-flex items-center justify-center">
            <Logo variant="icon" size="xl" />
          </div>
          
          <div className="space-y-1.5">
            <h1 className="text-2xl font-black tracking-tight text-white sm:text-3xl">
              Sign in to <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">TestPilot AI</span>
            </h1>
            <p className="text-xs sm:text-sm text-gray-400 font-medium max-w-xs mx-auto leading-relaxed">
              Autonomous Regression Testing & Code Intelligence Platform
            </p>
          </div>
        </div>

        {/* Action Button */}
        <div className="space-y-4 pt-1">
          <button
            onClick={handleGitHubLogin}
            disabled={loading}
            className="w-full flex justify-center items-center gap-3 px-5 py-3.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold rounded-xl border border-blue-400/30 disabled:opacity-50 transition-all duration-200 text-sm shadow-xl shadow-blue-950/40 hover:shadow-blue-600/30 hover:scale-[1.01] active:scale-[0.98]"
          >
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
            </svg>
            <span>{loading ? "Connecting to GitHub..." : "Continue with GitHub OAuth"}</span>
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-medium">
            {error}
          </div>
        )}

        {/* Footer Security Note */}
        <div className="pt-2 border-t border-white/5 text-[11px] text-zinc-500 flex items-center justify-center gap-1.5 font-medium">
          <svg className="w-3.5 h-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span>Secured by GitHub OAuth • Zero password storage</span>
        </div>
      </div>
    </div>
  );
}
