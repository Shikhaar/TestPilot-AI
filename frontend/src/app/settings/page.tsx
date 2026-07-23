"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { usersApi, UserSettings } from "@/lib/api/users";

type SaveState = "idle" | "saving" | "saved" | "error";

export default function SettingsPage() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [keyInput, setKeyInput] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [clearState, setClearState] = useState<"idle" | "clearing" | "cleared">("idle");

  useEffect(() => {
    usersApi
      .getSettings()
      .then((s) => setSettings(s))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    if (!keyInput.trim()) return;
    setSaveState("saving");
    setErrorMsg("");
    try {
      const updated = await usersApi.updateSettings({ gemini_api_key: keyInput.trim() });
      setSettings(updated);
      setKeyInput("");
      setSaveState("saved");
      setTimeout(() => setSaveState("idle"), 3000);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save key";
      setErrorMsg(message);
      setSaveState("error");
      setTimeout(() => setSaveState("idle"), 4000);
    }
  }

  async function handleClear() {
    setClearState("clearing");
    try {
      const updated = await usersApi.clearGeminiKey();
      setSettings(updated);
      setClearState("cleared");
      setTimeout(() => setClearState("idle"), 3000);
    } catch {
      setClearState("idle");
    }
  }

  return (
    <div className="flex h-screen bg-[#06070a] text-white overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-y-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white tracking-tight">Settings</h1>
          <p className="text-gray-400 mt-1 text-sm">
            Manage your account preferences and API integrations.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="max-w-2xl space-y-6">

            {/* Profile Card */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-6">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Profile
              </h2>
              <div className="flex items-center gap-4">
                {settings?.avatar_url ? (
                  <img
                    src={settings.avatar_url}
                    alt={settings.name ?? settings.username}
                    className="w-14 h-14 rounded-full border-2 border-purple-500/30"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-full bg-purple-600/20 flex items-center justify-center text-xl font-bold text-purple-300">
                    {settings?.username?.charAt(0).toUpperCase() ?? "?"}
                  </div>
                )}
                <div>
                  <p className="font-semibold text-white">{settings?.name ?? settings?.username ?? "—"}</p>
                  <p className="text-sm text-gray-400">@{settings?.username}</p>
                  <p className="text-xs text-gray-500">{settings?.email ?? "No email"}</p>
                </div>
                <span className="ml-auto px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 capitalize">
                  {settings?.role ?? "member"}
                </span>
              </div>
            </div>

            {/* Gemini API Key Card */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-6">
              <h2 className="text-lg font-semibold text-white mb-1 flex items-center gap-2">
                <svg className="w-5 h-5 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
                Gemini API Key
                <span className="ml-2 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
                  BYOK
                </span>
              </h2>
              <p className="text-sm text-gray-400 mb-5">
                TestPilot AI uses your personal Gemini API key to run AI test generation and PR risk analysis.
                Your key is never shared and only used for your requests.{" "}
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:underline"
                >
                  Get a free key →
                </a>
              </p>

              {/* Current key status */}
              <div className="mb-5 rounded-xl border border-white/5 bg-black/30 p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Current key</p>
                  {settings?.has_gemini_api_key ? (
                    <p className="text-sm font-mono text-green-400">
                      {settings.gemini_api_key_preview}
                    </p>
                  ) : (
                    <p className="text-sm text-gray-500 italic">No key saved</p>
                  )}
                </div>
                {settings?.has_gemini_api_key && (
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1.5 text-xs text-green-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                      Active
                    </span>
                    <button
                      onClick={handleClear}
                      disabled={clearState === "clearing"}
                      className="text-xs px-3 py-1.5 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 transition disabled:opacity-50"
                    >
                      {clearState === "clearing" ? "Clearing..." : clearState === "cleared" ? "Cleared ✓" : "Remove"}
                    </button>
                  </div>
                )}
              </div>

              {/* Input new key */}
              <div className="space-y-3">
                <label className="block text-xs font-medium text-gray-400 uppercase tracking-wider">
                  {settings?.has_gemini_api_key ? "Replace Key" : "Add Key"}
                </label>
                <div className="flex gap-3">
                  <div className="relative flex-1">
                    <input
                      id="gemini-api-key-input"
                      type={showKey ? "text" : "password"}
                      value={keyInput}
                      onChange={(e) => setKeyInput(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSave()}
                      placeholder="AIzaSy••••••••••••••••••••••••••••••••••"
                      className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm font-mono text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition pr-12"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey((s) => !s)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition"
                      title={showKey ? "Hide key" : "Show key"}
                    >
                      {showKey ? (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      )}
                    </button>
                  </div>

                  <button
                    id="save-gemini-key-btn"
                    onClick={handleSave}
                    disabled={!keyInput.trim() || saveState === "saving"}
                    className={`px-5 py-3 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 ${
                      saveState === "saved"
                        ? "bg-green-600 text-white"
                        : saveState === "error"
                        ? "bg-red-600 text-white"
                        : "bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    }`}
                  >
                    {saveState === "saving" && (
                      <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    )}
                    {saveState === "saved" ? "Saved ✓" : saveState === "error" ? "Error" : "Save Key"}
                  </button>
                </div>

                {errorMsg && (
                  <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                    {errorMsg}
                  </p>
                )}

                <p className="text-xs text-gray-600">
                  Your key is stored encrypted and never exposed in API responses. It is used exclusively for your test generation and PR analysis requests.
                </p>
              </div>
            </div>

            {/* Danger Zone */}
            <div className="rounded-2xl border border-red-500/10 bg-red-500/[0.02] p-6">
              <h2 className="text-lg font-semibold text-red-400 mb-1 flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Danger Zone
              </h2>
              <p className="text-sm text-gray-500 mb-4">
                Removing your Gemini API key will disable all AI test generation features until you add a new one.
              </p>
              <button
                onClick={handleClear}
                disabled={!settings?.has_gemini_api_key || clearState === "clearing"}
                className="px-4 py-2 rounded-lg border border-red-500/30 text-red-400 text-sm hover:bg-red-500/10 transition disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {clearState === "clearing" ? "Removing..." : "Remove Gemini API Key"}
              </button>
            </div>

          </div>
        )}
      </main>
    </div>
  );
}
