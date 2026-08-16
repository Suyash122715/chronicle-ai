"use client";

import React, { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import GuestGuard from "@/components/auth/GuestGuard";
import LoginForm from "@/components/auth/LoginForm";
import Alert from "@/components/ui/Alert";

function LoginContent() {
  const searchParams = useSearchParams();
  const isRegistered = searchParams.get("registered") === "true";

  return (
    <div className="flex min-h-screen w-full flex-col items-center justify-center bg-slate-950 p-4 sm:p-8">
      <div className="w-full max-w-md space-y-4">
        {isRegistered && (
          <Alert
            variant="success"
            message="Account created successfully! Please sign in with your credentials."
          />
        )}
        <LoginForm />
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <GuestGuard>
      <Suspense
        fallback={
          <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
          </div>
        }
      >
        <LoginContent />
      </Suspense>
    </GuestGuard>
  );
}
