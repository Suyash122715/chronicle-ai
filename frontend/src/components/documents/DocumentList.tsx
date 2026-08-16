"use client";

import React, { useState } from "react";
import { useArtifacts } from "@/hooks/useArtifacts";
import DocumentCard from "@/components/documents/DocumentCard";
import EmptyDocuments from "@/components/documents/EmptyDocuments";
import { Input } from "@/components/ui/Input";
import { Alert } from "@/components/ui/Alert";
import { Search, SlidersHorizontal } from "lucide-react";

interface DocumentListProps {
  onUploadClick: () => void;
}

export function DocumentList({ onUploadClick }: DocumentListProps) {
  const { data: artifacts, isLoading, isError, error } = useArtifacts();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");

  const filteredArtifacts = (artifacts || []).filter((artifact) => {
    const matchesSearch =
      artifact.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (artifact.document_type || "").toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      selectedStatus === "all" || artifact.status === selectedStatus;

    return matchesSearch && matchesStatus;
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((n) => (
          <div
            key={n}
            className="h-44 rounded-xl border border-slate-800 bg-slate-900/30 p-5 space-y-4 animate-pulse"
          >
            <div className="flex justify-between items-center">
              <div className="h-5 w-20 rounded bg-slate-800" />
              <div className="h-5 w-16 rounded-full bg-slate-800" />
            </div>
            <div className="h-4 w-3/4 rounded bg-slate-800" />
            <div className="h-3 w-1/2 rounded bg-slate-800" />
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <Alert
        variant="error"
        message={error?.message || "Failed to load document list. Please try again."}
      />
    );
  }

  if (!artifacts || artifacts.length === 0) {
    return <EmptyDocuments onUploadClick={onUploadClick} />;
  }

  return (
    <div className="space-y-6">
      {/* Search and Status Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <Input
            type="text"
            placeholder="Search documents by name or type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-900 border-slate-800"
          />
        </div>

        <div className="flex items-center space-x-2">
          <SlidersHorizontal className="h-4 w-4 text-slate-400" />
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="h-10 rounded-md border border-slate-800 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="all">All Statuses ({artifacts.length})</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Grid of Documents */}
      {filteredArtifacts.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-8 text-center text-slate-400 text-sm">
          No documents match your search query &quot;{searchQuery}&quot;.
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredArtifacts.map((artifact) => (
            <DocumentCard key={artifact.id} artifact={artifact} />
          ))}
        </div>
      )}
    </div>
  );
}

export default DocumentList;
