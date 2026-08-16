import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "error" | "success" | "info";
  message: string;
}

export function Alert({ variant = "error", message, className, ...props }: AlertProps) {
  const styles = {
    error: "border-rose-900/50 bg-rose-950/30 text-rose-300",
    success: "border-emerald-900/50 bg-emerald-950/30 text-emerald-300",
    info: "border-sky-900/50 bg-sky-950/30 text-sky-300",
  };

  const icons = {
    error: <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />,
    success: <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />,
    info: <Info className="h-4 w-4 shrink-0 text-sky-400" />,
  };

  return (
    <div
      className={twMerge(
        clsx(
          "flex items-start space-x-3 rounded-lg border p-3.5 text-sm font-medium transition-all duration-200",
          styles[variant],
          className
        )
      )}
      {...props}
    >
      <div className="mt-0.5">{icons[variant]}</div>
      <div className="flex-1 break-words">{message}</div>
    </div>
  );
}

export default Alert;
