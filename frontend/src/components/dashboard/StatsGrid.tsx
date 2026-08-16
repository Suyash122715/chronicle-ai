"use client";

import React from "react";
import StatCard from "@/components/dashboard/StatCard";
import { useArtifacts } from "@/hooks/useArtifacts";
import { FileText, Loader2, CheckCircle2, Network } from "lucide-react";

export function StatsGrid() {
  const { data: artifacts, isLoading } = useArtifacts();

  const totalCount = isLoading || !artifacts ? "—" : String(artifacts.length);

  const processingCount =
    isLoading || !artifacts
      ? "—"
      : String(
          artifacts.filter(
            (a) => a.status === "pending" || a.status === "processing"
          ).length
        );

  const completedCount =
    isLoading || !artifacts
      ? "—"
      : String(artifacts.filter((a) => a.status === "completed").length);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        title="Total Documents"
        value={totalCount}
        subtitle="Uploaded career artifacts"
        icon={FileText}
        isPlaceholder={isLoading}
      />
      <StatCard
        title="Processing"
        value={processingCount}
        subtitle="Active entity extractions"
        icon={Loader2}
        isPlaceholder={isLoading}
      />
      <StatCard
        title="Completed"
        value={completedCount}
        subtitle="Processed extractions"
        icon={CheckCircle2}
        isPlaceholder={isLoading}
      />
      <StatCard
        title="Knowledge Items"
        value="—"
        subtitle="Extracted entities & skills"
        icon={Network}
        isPlaceholder={true}
      />
    </div>
  );
}

export default StatsGrid;
