"use client";

import React, { useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useResetPassword } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api";

function ResetForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const reset = useResetPassword();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError("Password is required");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setError("");
    reset.mutate(
      { token, password },
      {
        onError: (err) => setError(getErrorMessage(err)),
        onSuccess: () => setDone(true),
      }
    );
  };

  if (done) {
    return (
      <div className="text-center">
        <p className="text-sm text-muted-foreground mb-4">Your password has been reset successfully.</p>
        <Link href="/login" className="text-sm text-foreground hover:underline font-medium">
          Sign in with your new password
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      {error && (
        <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-sm text-destructive">
          {error}
        </div>
      )}

      <Input
        label="New Password"
        type="password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => { setPassword(e.target.value); setError(""); }}
        required
      />
      <Input
        label="Confirm Password"
        type="password"
        placeholder="••••••••"
        value={confirm}
        onChange={(e) => { setConfirm(e.target.value); setError(""); }}
        required
      />

      <Button type="submit" loading={reset.isPending} disabled={reset.isPending} className="w-full mt-2">
        Reset Password
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="border border-border bg-card rounded-xl p-8 w-full max-w-[400px] shadow-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-black text-xl mb-4">
            R
          </div>
          <h1 className="text-xl font-medium text-foreground tracking-tight">Set New Password</h1>
          <p className="text-muted-foreground text-sm mt-1">Enter your new password below</p>
        </div>

        <Suspense fallback={<div className="text-center text-sm text-muted-foreground">Loading...</div>}>
          <ResetForm />
        </Suspense>

        <p className="text-center text-xs text-muted-foreground mt-6">
          <Link href="/login" className="text-foreground hover:underline font-medium">
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  );
}