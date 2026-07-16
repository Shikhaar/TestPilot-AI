"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authApi } from "@/lib/api/auth";

function AuthCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState("Authenticating...");

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state") || undefined;

    if (!code) {
      setStatus("Error: Authorization code missing from callback parameters.");
      return;
    }

    async function exchangeToken() {
      try {
        await authApi.handleCallback(code!, state);
        setStatus("Authentication successful! Redirecting...");
        router.push("/");
      } catch (err) {
        console.error(err);
        setStatus("Failed to exchange authorization code. Please try logging in again.");
      }
    }

    exchangeToken();
  }, [searchParams, router]);

  return (
    <div className="text-center space-y-4">
      <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto" />
      <p className="text-sm text-gray-400 font-medium">{status}</p>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#030303]">
      <Suspense fallback={
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-gray-400 font-medium">Loading session...</p>
        </div>
      }>
        <AuthCallbackInner />
      </Suspense>
    </div>
  );
}
