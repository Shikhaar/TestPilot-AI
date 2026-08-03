"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api/auth";
import Logo from "@/components/Logo";

export default function Login() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState("");
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  const [gmailInput, setGmailInput] = useState("");

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

  const handleGoogleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setGoogleLoading(true);
    setError("");
    try {
      await authApi.googleLogin(gmailInput || undefined);
      router.push("/");
    } catch (err: any) {
      console.error("Google Login error:", err);
      const msg = err.response?.data?.detail || err.message || "Failed to sign in with Google";
      setError(msg);
    } finally {
      setGoogleLoading(false);
      setShowGoogleModal(false);
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

        {/* Action Buttons */}
        <div className="space-y-4 pt-1">
          {/* GitHub OAuth Button */}
          <button
            onClick={handleGitHubLogin}
            disabled={loading || googleLoading}
            className="w-full flex justify-center items-center gap-3 px-5 py-3.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold rounded-xl border border-blue-400/30 disabled:opacity-50 transition-all duration-200 text-sm shadow-xl shadow-blue-950/40 hover:shadow-blue-600/30 hover:scale-[1.01] active:scale-[0.98]"
          >
            <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.162 22 16.418 22 12c0-5.523-4.477-10-10-10z" />
            </svg>
            <span>{loading ? "Connecting to GitHub..." : "Continue with GitHub OAuth"}</span>
          </button>

          {/* Divider */}
          <div className="relative flex items-center py-1">
            <div className="flex-grow border-t border-white/10" />
            <span className="flex-shrink mx-4 text-[10px] uppercase tracking-widest text-zinc-500 font-bold">Or continue with</span>
            <div className="flex-grow border-t border-white/10" />
          </div>

          {/* Google / Gmail Sign In Button */}
          <button
            onClick={() => setShowGoogleModal(true)}
            disabled={loading || googleLoading}
            className="w-full flex justify-center items-center gap-3 px-5 py-3.5 bg-zinc-900/90 hover:bg-zinc-800 text-gray-200 font-semibold rounded-xl border border-zinc-800 hover:border-zinc-700 disabled:opacity-50 transition-all duration-200 text-sm shadow-md hover:scale-[1.01] active:scale-[0.98]"
          >
            {/* Google SVG Icon */}
            <svg className="w-4.5 h-4.5" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
            </svg>
            <span>{googleLoading ? "Signing in..." : "Continue with Google / Gmail"}</span>
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-medium">
            {error}
          </div>
        )}
      </div>

      {/* Google / Gmail Modal */}
      {showGoogleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-sm p-6 sm:p-7 rounded-2xl bg-zinc-950 border border-white/10 shadow-2xl space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                Sign in with Google
              </h3>
              <button
                onClick={() => setShowGoogleModal(false)}
                className="text-gray-500 hover:text-white text-lg font-bold transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleGoogleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-1.5">
                  Enter your Gmail / Google Address:
                </label>
                <input
                  type="email"
                  required
                  placeholder="name@gmail.com"
                  value={gmailInput}
                  onChange={(e) => setGmailInput(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-zinc-900 border border-white/10 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
                />
                <p className="text-[11px] text-gray-500 mt-2 leading-relaxed">
                  If this email is associated with your GitHub account, your workspace will be linked automatically.
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowGoogleModal(false)}
                  className="flex-1 py-3 bg-zinc-900 hover:bg-zinc-800 text-gray-300 text-xs font-semibold rounded-xl border border-white/10 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={googleLoading}
                  className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-900/30 transition-colors"
                >
                  {googleLoading ? "Signing in..." : "Continue"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
