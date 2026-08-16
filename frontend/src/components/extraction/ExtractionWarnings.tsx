import React from "react";
import { AlertTriangle } from "lucide-react";

interface ExtractionWarningsProps {
  warnings: string[];
}

export function ExtractionWarnings({ warnings }: ExtractionWarningsProps) {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="rounded-xl border border-amber-900/50 bg-amber-950/20 p-4 space-y-2">
      <div className="flex items-center space-x-2 text-amber-400 font-semibold text-xs uppercase tracking-wider">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>Extraction Warnings ({warnings.length})</span>
      </div>

      <ul className="space-y-1 pl-6 text-xs text-amber-300/90 list-disc">
        {warnings.map((warning, idx) => (
          <li key={idx} className="break-words">
            {warning}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ExtractionWarnings;
