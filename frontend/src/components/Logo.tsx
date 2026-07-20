"use client";

import React from "react";

interface LogoProps {
  variant?: "full" | "icon";
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

export default function Logo({ variant = "full", size = "md", className = "" }: LogoProps) {
  const sizeMap = {
    sm: { icon: "w-6 h-6", text: "text-sm", gap: "space-x-2" },
    md: { icon: "w-8 h-8", text: "text-base", gap: "space-x-2.5" },
    lg: { icon: "w-10 h-10", text: "text-xl", gap: "space-x-3" },
    xl: { icon: "w-12 h-12", text: "text-2xl", gap: "space-x-3.5" },
  };

  const currentSize = sizeMap[size] || sizeMap.md;

  return (
    <div className={`inline-flex items-center ${currentSize.gap} ${className}`}>
      {/* Brand Icon SVG */}
      <div className={`relative flex items-center justify-center ${currentSize.icon}`}>
        {/* Ambient Glow */}
        <div className="absolute inset-0 rounded-xl bg-gradient-to-tr from-purple-600 to-cyan-500 opacity-40 blur-sm transform scale-110" />
        
        {/* SVG Wings Symbol */}
        <svg
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="relative w-full h-full drop-shadow-md"
        >
          <defs>
            <linearGradient id="tp-grad-primary" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#9333EA" />
              <stop offset="50%" stopColor="#6366F1" />
              <stop offset="100%" stopColor="#06B6D4" />
            </linearGradient>
            <linearGradient id="tp-grad-accent" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#38BDF8" />
              <stop offset="100%" stopColor="#A855F7" />
            </linearGradient>
            <linearGradient id="tp-grad-wing" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#C084FC" stopOpacity="0.7" />
            </linearGradient>
          </defs>

          {/* Hexagonal Base Frame */}
          <rect
            x="2"
            y="2"
            width="36"
            height="36"
            rx="10"
            fill="#0B0C10"
            stroke="url(#tp-grad-primary)"
            strokeWidth="1.5"
            strokeOpacity="0.6"
          />

          {/* Supersonic Pilot Wing Left */}
          <path
            d="M 10 27 L 20 9 L 20 22 Z"
            fill="url(#tp-grad-primary)"
          />

          {/* Supersonic Pilot Wing Right */}
          <path
            d="M 30 27 L 20 9 L 20 22 Z"
            fill="url(#tp-grad-accent)"
          />

          {/* Center Flight Trajectory Line */}
          <path
            d="M 20 9 L 20 31"
            stroke="url(#tp-grad-wing)"
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* AI Neural Node Circles */}
          <circle cx="20" cy="9" r="2.5" fill="#FFFFFF" />
          <circle cx="10" cy="27" r="2" fill="#38BDF8" />
          <circle cx="30" cy="27" r="2" fill="#A855F7" />
          <circle cx="20" cy="31" r="1.5" fill="#FFFFFF" />
        </svg>
      </div>

      {/* Brand Text */}
      {variant === "full" && (
        <div className="flex flex-col leading-none">
          <span className={`font-extrabold tracking-tight bg-gradient-to-r from-white via-gray-100 to-purple-300 bg-clip-text text-transparent ${currentSize.text}`}>
            TestPilot <span className="bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">AI</span>
          </span>
          <span className="text-[9px] uppercase tracking-widest text-gray-500 font-semibold mt-0.5">
            Regression Engine
          </span>
        </div>
      )}
    </div>
  );
}
