"use client";

import React from "react";
import { useAuthStore } from "@/stores/authStore";

export function UserMenu() {
  const user = useAuthStore((state) => state.user);

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <div className="flex items-center space-x-3">
      <div className="hidden text-right sm:block">
        <p className="text-xs font-semibold text-white">{user?.full_name || "User"}</p>
        <p className="text-[11px] text-slate-400">{user?.email}</p>
      </div>
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-xs font-bold text-emerald-400 shadow-inner">
        {initials}
      </div>
    </div>
  );
}

export default UserMenu;
