import React from "react";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: LucideIcon;
  isPlaceholder?: boolean;
}

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  isPlaceholder = true,
}: StatCardProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 shadow-sm transition-colors hover:border-slate-700/80">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          {title}
        </span>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 border border-slate-700/50 text-slate-400">
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline space-x-2">
        <span className="text-3xl font-bold tracking-tight text-white">{value}</span>
        {isPlaceholder && (
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
            Coming soon
          </span>
        )}
      </div>

      <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
    </div>
  );
}

export default StatCard;
