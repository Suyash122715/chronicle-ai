"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authService } from "@/services/authService";
import { useAuthStore } from "@/stores/authStore";
import { ApiError } from "@/types/api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";
import { Alert } from "@/components/ui/Alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";

export function LoginForm() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const validate = () => {
    const newErrors: { email?: string; password?: string } = {};

    if (!email.trim()) {
      newErrors.email = "Email is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      newErrors.email = "Please enter a valid email address.";
    }

    if (!password) {
      newErrors.password = "Password is required.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setServerError(null);

    if (!validate()) return;

    setIsLoading(true);

    try {
      // 1. Authenticate user -> receive JWT access_token
      const tokenRes = await authService.login({
        email: email.trim(),
        password,
      });

      // Temporarily set token so client interceptor attaches it for getCurrentUser()
      if (typeof window !== "undefined") {
        localStorage.setItem("chronicle_access_token", tokenRes.access_token);
      }

      // 2. Retrieve authenticated user profile
      const user = await authService.getCurrentUser();

      // 3. Update Zustand auth store
      setAuth(tokenRes.access_token, user);

      // 4. Redirect to protected dashboard
      router.replace("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.detail);
      } else {
        setServerError("Failed to sign in. Please check your credentials and try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md border-slate-800 bg-slate-950/90 shadow-2xl">
      <CardHeader className="space-y-2 text-center sm:text-left">
        <CardTitle className="text-3xl font-bold tracking-tight text-white">
          Sign In
        </CardTitle>
        <CardDescription className="text-slate-400">
          Enter your email and password to access your Chronicle AI account.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          {serverError && <Alert variant="error" message={serverError} />}

          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              error={errors.email}
              disabled={isLoading}
              autoComplete="email"
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              disabled={isLoading}
              autoComplete="current-password"
            />
          </div>

          <Button type="submit" className="w-full" isLoading={isLoading} size="lg">
            Sign In
          </Button>

          <div className="text-center text-sm text-slate-400">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="font-semibold text-emerald-400 transition-colors hover:text-emerald-300 underline-offset-4 hover:underline"
            >
              Create an account
            </Link>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

export default LoginForm;
