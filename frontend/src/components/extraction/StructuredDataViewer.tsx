"use client";

import React, { useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check, Code, LayoutList } from "lucide-react";
import { clsx } from "clsx";

interface StructuredDataViewerProps {
  data: Record<string, unknown>;
}

// Utility to convert snake_case/camelCase keys into clean Human Titles
function formatKeyLabel(key: string): string {
  if (!key) return "";
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

// Recursive Value Renderer Component
function ValueRenderer({ value, depth = 0 }: { value: unknown; depth?: number }) {
  const [isOpen, setIsOpen] = useState(true);

  // 1. Primitive Null / Undefined
  if (value === null || value === undefined) {
    return <span className="text-slate-500 italic font-mono text-xs">null</span>;
  }

  // 2. Primitive Boolean
  if (typeof value === "boolean") {
    return (
      <span
        className={clsx(
          "font-mono text-xs font-semibold px-1.5 py-0.5 rounded",
          value
            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
            : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
        )}
      >
        {value ? "true" : "false"}
      </span>
    );
  }

  // 3. Primitive Number
  if (typeof value === "number") {
    return <span className="font-mono text-xs font-semibold text-sky-400">{value}</span>;
  }

  // 4. Primitive String
  if (typeof value === "string") {
    return <span className="text-slate-200 text-xs break-words">{value}</span>;
  }

  // 5. Array Rendering
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-slate-500 text-xs italic">[ Empty Array ]</span>;
    }

    const isPrimitiveArray = value.every(
      (item) =>
        typeof item === "string" || typeof item === "number" || typeof item === "boolean"
    );

    // If it's a array of short primitives (e.g. skills: ["Python", "React"]), display as tags!
    if (isPrimitiveArray) {
      return (
        <div className="flex flex-wrap gap-1.5 my-1">
          {value.map((item, idx) => (
            <span
              key={idx}
              className="inline-flex items-center rounded-md bg-slate-800 border border-slate-700/80 px-2 py-1 text-xs font-medium text-emerald-300"
            >
              {String(item)}
            </span>
          ))}
        </div>
      );
    }

    // Array of objects / complex items
    return (
      <div className="space-y-2 mt-1">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          {isOpen ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          <span className="font-mono font-medium">List ({value.length} items)</span>
        </button>

        {isOpen && (
          <div className="space-y-2 border-l-2 border-slate-800 pl-3 ml-1">
            {value.map((item, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-3 space-y-2"
              >
                <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
                  Item #{idx + 1}
                </div>
                <ValueRenderer value={item} depth={depth + 1} />
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // 6. Object Rendering
  if (typeof value === "object") {
    const keys = Object.keys(value as object);
    if (keys.length === 0) {
      return <span className="text-slate-500 text-xs italic">{"{ Empty Object }"}</span>;
    }

    return (
      <div className="space-y-2 w-full">
        {depth > 0 && (
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition-colors"
          >
            {isOpen ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
            <span className="font-medium text-slate-300">Object ({keys.length} fields)</span>
          </button>
        )}

        {isOpen && (
          <div
            className={clsx(
              "grid gap-3",
              depth > 0 && "border-l-2 border-slate-800/80 pl-3 ml-1"
            )}
          >
            {keys.map((key) => {
              const val = (value as Record<string, unknown>)[key];
              const isComplex = typeof val === "object" && val !== null;

              return (
                <div
                  key={key}
                  className={clsx(
                    "flex flex-col space-y-1 rounded-lg bg-slate-900/40 p-2.5 border border-slate-800/60",
                    isComplex ? "col-span-full" : ""
                  )}
                >
                  <span className="text-xs font-semibold text-emerald-400/90 tracking-wide">
                    {formatKeyLabel(key)}
                  </span>
                  <div className="mt-0.5">
                    <ValueRenderer value={val} depth={depth + 1} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  }

  return <span className="text-slate-300 text-xs">{String(value)}</span>;
}

export function StructuredDataViewer({ data }: StructuredDataViewerProps) {
  const [viewMode, setViewMode] = useState<"formatted" | "raw">("formatted");
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-8 text-center text-slate-400 text-xs">
        No structured data extracted.
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 space-y-4 shadow-md">
      {/* Header Controls */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <h3 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
          <span>Structured Entities</span>
          <span className="text-xs font-normal text-slate-400">
            ({Object.keys(data).length} top-level fields)
          </span>
        </h3>

        <div className="flex items-center space-x-2">
          {/* View Toggle */}
          <div className="flex items-center rounded-lg border border-slate-800 bg-slate-900 p-0.5">
            <button
              onClick={() => setViewMode("formatted")}
              className={clsx(
                "flex items-center space-x-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                viewMode === "formatted"
                  ? "bg-slate-800 text-emerald-400 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              )}
            >
              <LayoutList className="h-3.5 w-3.5" />
              <span>Formatted</span>
            </button>
            <button
              onClick={() => setViewMode("raw")}
              className={clsx(
                "flex items-center space-x-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                viewMode === "raw"
                  ? "bg-slate-800 text-emerald-400 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              )}
            >
              <Code className="h-3.5 w-3.5" />
              <span>JSON</span>
            </button>
          </div>

          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1.5 rounded-lg border border-slate-800 bg-slate-900 px-2.5 py-1 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition-colors"
            title="Copy structured JSON"
          >
            {copied ? (
              <>
                <Check className="h-3.5 w-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="h-3.5 w-3.5 text-slate-400" />
                <span>Copy JSON</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {viewMode === "formatted" ? (
        <div className="pt-1">
          <ValueRenderer value={data} depth={0} />
        </div>
      ) : (
        <pre className="max-h-96 overflow-y-auto rounded-lg bg-slate-900/90 p-4 font-mono text-xs text-emerald-300 border border-slate-800/80 whitespace-pre-wrap leading-relaxed">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default StructuredDataViewer;
