"use client";

import React from "react";
import { useAuthStore } from "@/stores/authStore";

export function WelcomeSection() {
  const user = useAuthStore((state) => state.user);
  const firstName = user?.full_name ? user.full_name.split(" ")[0] : "there";

  return (
    <div className="space-y-1">
      <h2 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
        Welcome back, {firstName} 👋
      </h2>
      <p className="text-sm text-slate-400 max-w-2xl">
        Chronicle AI is your Career Operating System — transforming your academic and professional artifacts into connected knowledge.
      </p>
    </div>
  );
}

export default WelcomeSection;
