"use client";

import React from "react";

interface LogoProps {
  variant?: "full" | "icon";
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

export default function Logo({ variant = "full", size = "md", className = "" }: LogoProps) {
  const sizeMap = {
    sm: { icon: "w-6 h-6", text: "text-sm", badge: "text-[9px] px-1 py-0.2", gap: "space-x-2" },
    md: { icon: "w-8 h-8", text: "text-base", badge: "text-[10px] px-1.5 py-0.5", gap: "space-x-2" },
    lg: { icon: "w-10 h-10", text: "text-xl", badge: "text-xs px-2 py-0.5", gap: "space-x-2.5" },
    xl: { icon: "w-12 h-12", text: "text-2xl", badge: "text-sm px-2.5 py-1", gap: "space-x-3" },
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
          className="w-full h-full drop-shadow-md"
        >
          {/* Left Speed Lines */}
          <path d="M 10 38 H 28" stroke="#2563EB" strokeWidth="5" strokeLinecap="round" />
          <path d="M 4 52 H 28" stroke="#2563EB" strokeWidth="5" strokeLinecap="round" />
          <path d="M 12 66 H 28" stroke="#2563EB" strokeWidth="5" strokeLinecap="round" />

          {/* Blue 'T' Top Bar & Diagonal Stem */}
          <path d="M 32 26 H 76" stroke="#2563EB" strokeWidth="11" strokeLinecap="round" />
          <circle cx="46" cy="38" r="4.5" fill="#2563EB" />
          <path d="M 58 26 L 44 84" stroke="#2563EB" strokeWidth="11" strokeLinecap="round" />

          {/* Dark Charcoal/Navy 'P' Loop & Leg */}
          <path
            d="M 54 26 H 74 C 90 26 90 60 74 60 H 54"
            stroke="#334155"
            strokeWidth="11"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path d="M 58 60 L 50 86" stroke="#334155" strokeWidth="11" strokeLinecap="round" />

          {/* Checkmark inside 'P' loop */}
          <path
            d="M 62 44 L 70 52 L 83 36"
            stroke="#2563EB"
            strokeWidth="5.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>
      </div>

      {/* Brand Text */}
      {variant === "full" && (
        <div className="flex flex-col leading-none">
          <div className="flex items-center space-x-1.5">
            <span className={`font-extrabold tracking-tight text-white ${currentSize.text}`}>
              Test<span className="text-blue-500">Pilot</span>
            </span>
            <span className={`font-bold text-blue-400 border border-blue-500/40 rounded-md bg-blue-500/10 ${currentSize.badge}`}>
              AI
            </span>
          </div>
          <span className="text-[8px] uppercase tracking-widest text-gray-400 font-medium mt-1">
            SMART TESTING. BETTER SOFTWARE.
          </span>
        </div>
      )}
    </div>
  );
}
