"use client";

import React from "react";

interface LogoProps {
  variant?: "full" | "icon";
  size?: "sm" | "md" | "lg" | "xl" | "2xl";
  className?: string;
}

export default function Logo({ variant = "full", size = "md", className = "" }: LogoProps) {
  const sizeMap = {
    sm: { icon: "w-6 h-6", text: "text-sm", badge: "text-[9px] px-1 py-0.2", gap: "space-x-2" },
    md: { icon: "w-8 h-8", text: "text-base", badge: "text-[10px] px-1.5 py-0.5", gap: "space-x-2" },
    lg: { icon: "w-10 h-10", text: "text-xl", badge: "text-xs px-2 py-0.5", gap: "space-x-2.5" },
    xl: { icon: "w-14 h-14", text: "text-2xl", badge: "text-sm px-2.5 py-1", gap: "space-x-3" },
    "2xl": { icon: "w-20 h-20", text: "text-3xl", badge: "text-base px-3 py-1", gap: "space-x-4" },
  };

  const currentSize = sizeMap[size] || sizeMap.md;

  return (
    <div className={`inline-flex items-center ${currentSize.gap} ${className}`}>
      {/* Brand Icon SVG */}
      <div className={`relative flex items-center justify-center ${currentSize.icon}`}>
        <svg
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full filter drop-shadow-[0_4px_12px_rgba(37,99,235,0.35)]"
        >
          <defs>
            {/* Speed Lines Gradient */}
            <linearGradient id="tpSpeedGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#60A5FA" />
              <stop offset="100%" stopColor="#2563EB" />
            </linearGradient>

            {/* Blue 'T' Stem Gradient */}
            <linearGradient id="tpBlueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#3B82F6" />
              <stop offset="100%" stopColor="#1D4ED8" />
            </linearGradient>

            {/* Metallic Slate 'P' Gradient */}
            <linearGradient id="tpSlateGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#CBD5E1" />
              <stop offset="100%" stopColor="#64748B" />
            </linearGradient>
          </defs>

          {/* 3 Left Speed Lines (Vibrant Blue/Cyan) */}
          <path d="M 18 36 H 36" stroke="url(#tpSpeedGrad)" strokeWidth="6.5" strokeLinecap="round" />
          <path d="M 12 50 H 36" stroke="url(#tpSpeedGrad)" strokeWidth="6.5" strokeLinecap="round" />
          <path d="M 18 64 H 36" stroke="url(#tpSpeedGrad)" strokeWidth="6.5" strokeLinecap="round" />

          {/* Slanted Blue 'T' Top & Stem */}
          <path d="M 32 23 H 48" stroke="url(#tpBlueGrad)" strokeWidth="13" strokeLinecap="round" />
          <path d="M 45 23 L 39 84" stroke="url(#tpBlueGrad)" strokeWidth="13" strokeLinecap="round" />

          {/* Slate Metallic 'P' Loop & Slanted Leg */}
          <path
            d="M 46 23 H 60 C 78 23 78 54 60 54 H 46"
            stroke="url(#tpSlateGrad)"
            strokeWidth="13"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path d="M 46 54 L 41 84" stroke="url(#tpSlateGrad)" strokeWidth="13" strokeLinecap="round" />
        </svg>
      </div>

      {/* Brand Text */}
      {variant === "full" && (
        <div className="flex flex-col leading-none">
          <div className="flex items-center space-x-2">
            <span className={`font-extrabold tracking-tight text-white ${currentSize.text}`}>
              Test<span className="text-blue-500">Pilot</span>
            </span>
            <span className={`font-bold text-blue-400 border border-blue-500/40 rounded-md bg-blue-500/10 shadow-sm ${currentSize.badge}`}>
              AI
            </span>
          </div>
          <span className="text-[8px] uppercase tracking-widest text-gray-400 font-semibold mt-1">
            SMART TESTING. BETTER SOFTWARE.
          </span>
        </div>
      )}
    </div>
  );
}
