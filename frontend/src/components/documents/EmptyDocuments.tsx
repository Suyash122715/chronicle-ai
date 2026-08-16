import React from "react";
import { FolderOpen, Upload } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface EmptyDocumentsProps {
  onUploadClick: () => void;
}

export function EmptyDocuments({ onUploadClick }: EmptyDocumentsProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 bg-slate-900/30 py-16 px-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-900 border border-slate-800 text-emerald-400 mb-4 shadow-inner">
        <FolderOpen className="h-8 w-8" />
      </div>

      <h3 className="text-base font-semibold text-white">No documents found</h3>
      <p className="mt-1 text-sm text-slate-400 max-w-md">
        You haven&apos;t uploaded any career artifacts yet. Upload resumes, certificates, marksheets, or project reports to begin organizing your career knowledge.
      </p>

      <Button variant="primary" size="md" className="mt-6" onClick={onUploadClick}>
        <Upload className="mr-2 h-4 w-4" />
        <span>Upload First Document</span>
      </Button>
    </div>
  );
}

export default EmptyDocuments;
