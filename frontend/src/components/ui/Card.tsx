import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Card({ className, ...props }: CardProps) {
  return (
    <div
      className={twMerge(
        clsx(
          "rounded-xl border border-slate-800 bg-slate-950/80 p-6 shadow-xl backdrop-blur-sm text-slate-100",
          className
        )
      )}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: CardProps) {
  return <div className={twMerge(clsx("mb-4 space-y-1.5", className))} {...props} />;
}

export function CardTitle({ className, children, ...props }: CardProps) {
  return (
    <h3
      className={twMerge(
        clsx("text-2xl font-bold tracking-tight text-white", className)
      )}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ className, children, ...props }: CardProps) {
  return (
    <p className={twMerge(clsx("text-sm text-slate-400", className))} {...props}>
      {children}
    </p>
  );
}

export function CardContent({ className, ...props }: CardProps) {
  return <div className={twMerge(clsx("space-y-4", className))} {...props} />;
}

export function CardFooter({ className, ...props }: CardProps) {
  return (
    <div
      className={twMerge(clsx("mt-6 flex items-center justify-between", className))}
      {...props}
    />
  );
}
