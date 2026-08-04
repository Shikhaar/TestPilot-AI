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
      {/* Exact Brand Icon SVG */}
      <div className={`relative flex items-center justify-center ${currentSize.icon}`}>
        <svg
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* 3 Left Speed Lines (Blue #2463EB) */}
          <path d="M 21 36 H 36" stroke="#2463EB" strokeWidth="6.5" strokeLinecap="round" />
          <path d="M 13 50 H 36" stroke="#2463EB" strokeWidth="6.5" strokeLinecap="round" />
          <path d="M 21 64 H 36" stroke="#2463EB" strokeWidth="6.5" strokeLinecap="round" />

          {/* Slanted Blue 'T' (#2463EB) */}
          <path d="M 33 23 H 47" stroke="#2463EB" strokeWidth="13" strokeLinecap="round" />
          <path d="M 45 23 L 39 84" stroke="#2463EB" strokeWidth="13" strokeLinecap="round" />

          {/* Slate Grey 'P' Loop & Leg (#5A6E85) */}
          <path
            d="M 46 23 H 59 C 77 23 77 54 59 54 H 46"
            stroke="#5A6E85"
            strokeWidth="13"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path d="M 46 54 L 41 84" stroke="#5A6E85" strokeWidth="13" strokeLinecap="round" />
        </svg>
      </div>

      {/* Brand Text */}
      {variant === "full" && (
        <div className="flex flex-col leading-none">
          <div className="flex items-center space-x-2">
            <span className={`font-extrabold tracking-tight text-white ${currentSize.text}`}>
              Test<span className="text-blue-500">Pilot</span>
            </span>
            <span className={`font-bold text-blue-400 border border-blue-500/40 rounded-md bg-blue-500/10 ${currentSize.badge}`}>
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
