"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authApi } from "@/lib/api/auth";

function AuthCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("Authenticating with GitHub...");
  const executedRef = useRef(false);

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state") || undefined;

    // Prevent double execution in React StrictMode
    if (executedRef.current) return;
    executedRef.current = true;

    if (!code) {
      console.error("Authorization code missing from callback parameters.");
      router.replace("/login");
      return;
    }

    async function exchangeToken() {
      try {
        await authApi.handleCallback(code!, state);
        router.push("/");
      } catch (err: unknown) {
        console.error("GitHub OAuth Callback error:", err);

        let detail = "Failed to exchange authorization code";

        if (err instanceof Error) {
          detail = err.message;
        } else if (
          typeof err === "object" &&
          err !== null &&
          "response" in err
        ) {
          const response = (err as {
            response?: {
              data?: {
                detail?: string;
              };
            };
          }).response;

          detail = response?.data?.detail || detail;
        }

        setStatus(
          `Authentication error: ${detail}. Please try logging in again.`,
        );
      }
    }

    exchangeToken();
  }, [searchParams, router]);

  return (
    <div className="text-center space-y-4 p-8 max-w-sm rounded-2xl bg-zinc-950/80 border border-white/10 shadow-2xl backdrop-blur-xl">
      <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
      <p className="text-sm text-gray-300 font-medium">{status}</p>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#030303]">
      <Suspense fallback={
        <div className="text-center space-y-4">
          <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-gray-400 font-medium">Loading session...</p>
        </div>
      }>
        <AuthCallbackInner />
      </Suspense>
    </div>
  );
}
