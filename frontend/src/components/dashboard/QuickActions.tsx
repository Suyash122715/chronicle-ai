import React from "react";
import Link from "next/link";
import { Upload, Files, Network, ArrowRight } from "lucide-react";

export function QuickActions() {
  const actions = [
    {
      title: "Upload Artifact",
      description: "Upload resumes, certificates, and marksheets for extraction",
      icon: Upload,
      href: "/documents",
      badge: "Batch 4",
      active: true,
    },
    {
      title: "View Documents",
      description: "Browse and inspect classified documents & extractions",
      icon: Files,
      href: "/documents",
      badge: "Batch 5",
      active: true,
    },
    {
      title: "Knowledge Graph",
      description: "Explore interconnected career entities & skill mappings",
      icon: Network,
      href: "#",
      badge: "Phase 5",
      active: false,
    },
  ];

  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold text-white">Quick Actions</h3>

      <div className="grid gap-4 sm:grid-cols-3">
        {actions.map((action) => {
          const Icon = action.icon;
          const isLink = action.active && action.href !== "#";

          const CardContent = (
            <div className="group relative flex flex-col justify-between h-full rounded-xl border border-slate-800 bg-slate-900/40 p-5 transition-all duration-200 hover:border-slate-700 hover:bg-slate-900/70">
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 border border-slate-700/60 text-emerald-400">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-semibold text-slate-400 border border-slate-700">
                    {action.badge}
                  </span>
                </div>

                <h4 className="mt-4 text-sm font-semibold text-white group-hover:text-emerald-300 transition-colors">
                  {action.title}
                </h4>
                <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                  {action.description}
                </p>
              </div>

              <div className="mt-4 flex items-center text-xs font-medium text-emerald-400 opacity-80 group-hover:opacity-100 transition-opacity">
                <span>Access</span>
                <ArrowRight className="ml-1 h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
              </div>
            </div>
          );

          if (isLink) {
            return (
              <Link key={action.title} href={action.href}>
                {CardContent}
              </Link>
            );
          }

          return (
            <div key={action.title} className="opacity-75 cursor-not-allowed">
              {CardContent}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default QuickActions;
