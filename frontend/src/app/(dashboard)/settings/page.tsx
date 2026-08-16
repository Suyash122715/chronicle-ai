import React from "react";
import { Sliders, Bell, Lock, Palette } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";

export default function SettingsPage() {
  const sections = [
    {
      title: "Preferences",
      description: "Customize theme, language, and workspace layout",
      icon: Palette,
    },
    {
      title: "Notifications",
      description: "Manage email alerts and processing status updates",
      icon: Bell,
    },
    {
      title: "Security",
      description: "Manage credentials and access tokens",
      icon: Lock,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold tracking-tight text-white">Settings</h2>
        <p className="text-sm text-slate-400">
          Configure application preferences and platform settings.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3 max-w-5xl">
        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <Card key={section.title} className="border-slate-800 bg-slate-900/40">
              <CardHeader>
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-800 border border-slate-700/60 text-emerald-400 mb-2">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle className="text-lg">{section.title}</CardTitle>
                <CardDescription>{section.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <span className="inline-block rounded bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-400 border border-slate-700">
                  Coming soon
                </span>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
