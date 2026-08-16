"use client";

import React, { useState } from "react";
import DocumentList from "@/components/documents/DocumentList";
import UploadDropzone from "@/components/documents/UploadDropzone";
import { Button } from "@/components/ui/Button";
import { Upload, X } from "lucide-react";

export default function DocumentsPage() {
  const [showUpload, setShowUpload] = useState(false);

  return (
    <div className="space-y-6">
      {/* Top Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Documents</h2>
          <p className="text-sm text-slate-400">
            Upload and manage the documents that power your ChronicleAI knowledge base.
          </p>
        </div>

        <Button
          variant={showUpload ? "secondary" : "primary"}
          size="md"
          onClick={() => setShowUpload(!showUpload)}
          className="shrink-0"
        >
          {showUpload ? (
            <>
              <X className="mr-2 h-4 w-4" />
              <span>Close Upload</span>
            </>
          ) : (
            <>
              <Upload className="mr-2 h-4 w-4" />
              <span>Upload Document</span>
            </>
          )}
        </Button>
      </div>

      {/* Expandable Upload Dropzone */}
      {showUpload && (
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h3 className="text-base font-semibold text-white">Upload New Artifact</h3>
            <span className="text-xs text-slate-400">Max size: 10 MB</span>
          </div>
          <UploadDropzone onSuccess={() => setShowUpload(false)} />
        </div>
      )}

      {/* Document List View */}
      <DocumentList onUploadClick={() => setShowUpload(true)} />
    </div>
  );
}
