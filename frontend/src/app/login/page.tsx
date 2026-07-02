"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useLogin } from "@/hooks/use-auth";
import { useBrandingStore } from "@/stores/branding-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FormErrors {
  email?: string;
  password?: string;
  server?: string;
}

export default function LoginPage() {
  const [email, setEmail] = useState("admin@reputationos.ai");
  const [password, setPassword] = useState("demo1234");
  const [errors, setErrors] = useState<FormErrors>({});
  const login = useLogin();
  const config = useBrandingStore((state) => state.brandingConfig);
  const brandName = config?.company_name || "ReputationOS AI";

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!EMAIL_REGEX.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }
    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    if (!validate()) return;
    login.mutate(
      { email, password },
      {
        onError: (error) => {
          const msg = getErrorMessage(error, "Invalid email or password");
          setErrors((prev) => ({ ...prev, server: msg }));
        },
      }
    );
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="border border-border bg-card rounded-xl p-8 w-full max-w-[400px] shadow-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-black text-xl mb-4">
            R
          </div>
          <h1 className="text-xl font-medium text-foreground tracking-tight">
            {brandName}
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {errors.server && (
            <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-sm text-destructive">
              {errors.server}
            </div>
          )}

          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setErrors((prev) => ({ ...prev, email: undefined, server: undefined })); }}
            error={errors.email}
            required
          />
          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setErrors((prev) => ({ ...prev, password: undefined, server: undefined })); }}
            error={errors.password}
            required
          />

          <Button type="submit" loading={login.isPending} disabled={login.isPending} className="w-full mt-2">
            Sign In
          </Button>
        </form>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-foreground hover:underline font-medium">
            Register
          </Link>
        </p>

        <div className="mt-6 p-3 rounded-md bg-accent/50 border border-border">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium mb-1">Demo Credentials</p>
          <p className="text-xs text-muted-foreground font-mono">admin@reputationos.ai / demo1234</p>
        </div>
      </div>
    </div>
  );
}
