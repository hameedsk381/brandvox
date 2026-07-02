"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useLogin, useVerifyMfaLogin } from "@/hooks/use-auth";
import { useBrandingStore } from "@/stores/branding-store";
import { useAuthStore } from "@/stores/auth-store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FormErrors {
  email?: string;
  password?: string;
  code?: string;
  server?: string;
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("admin@reputationos.ai");
  const [password, setPassword] = useState("demo1234");
  const [code, setCode] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const login = useLogin();
  const verifyMfa = useVerifyMfaLogin();
  const mfaToken = useAuthStore((state) => state.mfaToken);
  const showMfa = searchParams.get("mfa") === "1" && !!mfaToken;

  useEffect(() => {
    if (searchParams.get("msg") === "session_expired") {
      setErrors({ server: "Your session has expired. Please sign in again." });
    }
  }, [searchParams]);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (showMfa) {
      if (!code.trim()) newErrors.code = "Authentication code is required";
    } else {
      if (!email.trim()) newErrors.email = "Email is required";
      else if (!EMAIL_REGEX.test(email)) newErrors.email = "Please enter a valid email address";
      if (!password) newErrors.password = "Password is required";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    if (!validate()) return;

    if (showMfa) {
      verifyMfa.mutate(
        { mfa_token: mfaToken!, code },
        { onError: (error) => setErrors((prev) => ({ ...prev, code: getErrorMessage(error, "Invalid code") })) }
      );
    } else {
      login.mutate(
        { email, password },
        { onError: (error) => setErrors((prev) => ({ ...prev, server: getErrorMessage(error, "Invalid email or password") })) }
      );
    }
  };

  const brandName = useBrandingStore((state) => state.brandingConfig)?.company_name || "ReputationOS AI";

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="border border-border bg-card rounded-xl p-8 w-full max-w-[400px] shadow-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-black text-xl mb-4">
            R
          </div>
          <h1 className="text-xl font-medium text-foreground tracking-tight">{brandName}</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {showMfa ? "Enter your authentication code" : "Sign in to your account"}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {errors.server && (
            <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-sm text-destructive">
              {errors.server}
            </div>
          )}
          {showMfa ? (
            <Input label="Authentication Code" placeholder="000000" value={code}
              onChange={(e) => { setCode(e.target.value); setErrors((prev) => ({ ...prev, code: undefined })); }}
              error={errors.code} required maxLength={6} />
          ) : (
            <>
              <Input label="Email" type="email" placeholder="you@example.com" value={email}
                onChange={(e) => { setEmail(e.target.value); setErrors((prev) => ({ ...prev, email: undefined, server: undefined })); }}
                error={errors.email} required />
              <Input label="Password" type="password" placeholder="••••••••" value={password}
                onChange={(e) => { setPassword(e.target.value); setErrors((prev) => ({ ...prev, password: undefined, server: undefined })); }}
                error={errors.password} required />
            </>
          )}
          <Button type="submit" loading={login.isPending || verifyMfa.isPending} className="w-full mt-2">
            {showMfa ? "Verify" : "Sign In"}
          </Button>
        </form>

        {!showMfa && (
          <div className="text-center mt-4">
            <Link href="/forgot-password" className="text-xs text-muted-foreground hover:text-foreground hover:underline">
              Forgot your password?
            </Link>
          </div>
        )}
        {!showMfa && (
          <p className="text-center text-xs text-muted-foreground mt-4">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="text-foreground hover:underline font-medium">Register</Link>
          </p>
        )}
        {showMfa && (
          <p className="text-center text-xs text-muted-foreground mt-4">
            <button onClick={() => { useAuthStore.getState().clearMfaToken(); router.push("/login"); }}
              className="text-foreground hover:underline font-medium bg-transparent border-none cursor-pointer">
              Back to sign in
            </button>
          </p>
        )}
        {!showMfa && (
          <div className="mt-6 p-3 rounded-md bg-accent/50 border border-border">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium mb-1">Demo Credentials</p>
            <p className="text-xs text-muted-foreground font-mono">admin@reputationos.ai / demo1234</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center text-sm text-muted-foreground">Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}