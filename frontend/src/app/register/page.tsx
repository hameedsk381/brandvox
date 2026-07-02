"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRegister } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface FormErrors {
  name?: string;
  email?: string;
  password?: string;
  server?: string;
}

export default function RegisterPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});
  const register = useRegister();

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!name.trim()) {
      newErrors.name = "Name is required";
    }
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
    register.mutate(
      { name, email, password },
      {
        onError: (error) => {
          const msg = getErrorMessage(error, "Registration failed");
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
            ReputationOS AI
          </h1>
          <p className="text-muted-foreground text-sm mt-1">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {errors.server && (
            <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-sm text-destructive">
              {errors.server}
            </div>
          )}

          <Input
            label="Full Name"
            placeholder="John Doe"
            value={name}
            onChange={(e) => { setName(e.target.value); setErrors((prev) => ({ ...prev, name: undefined, server: undefined })); }}
            error={errors.name}
            required
          />
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
          <Button type="submit" loading={register.isPending} disabled={register.isPending} className="w-full mt-2">
            Create Account
          </Button>
        </form>

        <p className="text-center text-xs text-muted-foreground mt-6">
          Already have an account?{" "}
          <Link href="/login" className="text-foreground hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
