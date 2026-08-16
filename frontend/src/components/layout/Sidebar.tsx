"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/authStore";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import {
  LayoutDashboard,
  FileText,
  User,
  Settings,
  LogOut,
  Sparkles,
} from "lucide-react";

interface SidebarProps {
  className?: string;
  onNavigate?: () => void;
}

export const NAVIGATION_ITEMS = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Profile", href: "/profile", icon: User },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar({ className, onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearAuth } = useAuthStore();

  const handleLogout = () => {
    clearAuth();
    router.replace("/login");
  };

  const userInitials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <aside
      className={twMerge(
        clsx(
          "flex w-64 flex-col justify-between border-r border-slate-800 bg-slate-950 p-4 text-slate-300",
          className
        )
      )}
    >
      {/* Top Branding Section */}
      <div className="space-y-6">
        <div className="flex items-center space-x-3 px-2 py-1">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-700 text-white font-bold shadow-lg shadow-emerald-950/40">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-base font-bold tracking-tight text-white">
                Chronicle AI
              </span>
              <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-400 border border-emerald-500/20">
                v0.5
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Career OS</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1">
          {NAVIGATION_ITEMS.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={onNavigate}
                className={clsx(
                  "flex items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                )}
              >
                <Icon
                  className={clsx(
                    "h-4 w-4 shrink-0 transition-colors",
                    isActive ? "text-emerald-400" : "text-slate-500"
                  )}
                />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User Footer Section */}
      <div className="space-y-3 border-t border-slate-800/80 pt-4">
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-xs font-bold text-emerald-400">
              {userInitials}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-white">
                {user?.full_name || "User"}
              </p>
              <p className="truncate text-[11px] text-slate-500">{user?.email}</p>
            </div>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="flex w-full items-center space-x-3 rounded-lg px-3 py-2 text-xs font-medium text-slate-400 transition-colors hover:bg-rose-950/40 hover:text-rose-300 border border-transparent hover:border-rose-900/50"
        >
          <LogOut className="h-4 w-4 shrink-0 text-slate-500" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
