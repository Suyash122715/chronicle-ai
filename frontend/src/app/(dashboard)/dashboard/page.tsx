import React from "react";
import WelcomeSection from "@/components/dashboard/WelcomeSection";
import StatsGrid from "@/components/dashboard/StatsGrid";
import QuickActions from "@/components/dashboard/QuickActions";
import RecentDocuments from "@/components/dashboard/RecentDocuments";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <WelcomeSection />
      <StatsGrid />
      <QuickActions />
      <RecentDocuments />
    </div>
  );
}
