"use client";

import React from "react";
import GuestGuard from "@/components/auth/GuestGuard";
import RegisterForm from "@/components/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <GuestGuard>
      <div className="flex min-h-screen w-full flex-col items-center justify-center bg-slate-950 p-4 sm:p-8">
        <RegisterForm />
      </div>
    </GuestGuard>
  );
}
