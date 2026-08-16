"use client";

import React from "react";
import { useAuthStore } from "@/stores/authStore";
import { User, Mail, ShieldCheck, Calendar } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { formatDate } from "@/lib/utils/formatters";

export default function ProfilePage() {
  const user = useAuthStore((state) => state.user);

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold tracking-tight text-white">User Profile</h2>
        <p className="text-sm text-slate-400">
          View your Chronicle AI account details and authentication state.
        </p>
      </div>

      <Card className="max-w-2xl border-slate-800 bg-slate-900/50">
        <CardHeader>
          <div className="flex items-center space-x-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/10 border border-emerald-500/30 text-xl font-bold text-emerald-400">
              {user?.full_name
                ? user.full_name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase()
                    .slice(0, 2)
                : "U"}
            </div>
            <div>
              <CardTitle className="text-xl">{user?.full_name || "User"}</CardTitle>
              <CardDescription>{user?.email}</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 pt-4 border-t border-slate-800/80">
          <div className="flex items-center justify-between text-sm py-2 border-b border-slate-800/50">
            <span className="flex items-center space-x-2 text-slate-400">
              <User className="h-4 w-4 text-slate-500" />
              <span>Full Name</span>
            </span>
            <span className="font-medium text-white">{user?.full_name}</span>
          </div>

          <div className="flex items-center justify-between text-sm py-2 border-b border-slate-800/50">
            <span className="flex items-center space-x-2 text-slate-400">
              <Mail className="h-4 w-4 text-slate-500" />
              <span>Email Address</span>
            </span>
            <span className="font-medium text-white">{user?.email}</span>
          </div>

          <div className="flex items-center justify-between text-sm py-2 border-b border-slate-800/50">
            <span className="flex items-center space-x-2 text-slate-400">
              <ShieldCheck className="h-4 w-4 text-slate-500" />
              <span>Account Status</span>
            </span>
            <span className="inline-flex items-center space-x-1 text-emerald-400 text-xs font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
              Active User
            </span>
          </div>

          <div className="flex items-center justify-between text-sm py-2">
            <span className="flex items-center space-x-2 text-slate-400">
              <Calendar className="h-4 w-4 text-slate-500" />
              <span>Member Since</span>
            </span>
            <span className="font-medium text-slate-300">
              {formatDate(user?.created_at)}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
