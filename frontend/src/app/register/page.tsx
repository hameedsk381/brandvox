"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRegister } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getErrorMessage } from "@/lib/api";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function getPasswordStrength(pw: string): { label: string; color: string; width: string } {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'/`~]/.test(pw)) score++;
  if (pw.length >= 12) score++;
  const map = [
    { label: "Weak", color: "bg-destructive", width: "16%" },
    { label: "Fair", color: "bg-orange-400", width: "33%" },
    { label: "Good", color: "bg-amber-400", width: "50%" },
    { label: "Strong", color: "bg-lime-400", width: "66%" },
    { label: "Very Strong", color: "bg-emerald-400", width: "83%" },
    { label: "Excellent", color: "bg-emerald-500", width: "100%" },
  ];
  return map[Math.min(score, map.length - 1)];
}

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
  const strength = password ? getPasswordStrength(password) : null;

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!name.trim()) newErrors.name = "Name is required";
    if (!email.trim()) newErrors.email = "Email is required";
    else if (!EMAIL_REGEX.test(email)) newErrors.email = "Please enter a valid email address";
    if (!password) newErrors.password = "Password is required";
    else if (password.length < 8) newErrors.password = "Password must be at least 8 characters";
    else if (!/[A-Z]/.test(password)) newErrors.password = "Password needs an uppercase letter";
    else if (!/[a-z]/.test(password)) newErrors.password = "Password needs a lowercase letter";
    else if (!/\d/.test(password)) newErrors.password = "Password needs a digit";
    else if (!/[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;'/`~]/.test(password)) newErrors.password = "Password needs a special character";
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
          <h1 className="text-xl font-medium text-foreground tracking-tight">ReputationOS AI</h1>
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
          <div>
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setErrors((prev) => ({ ...prev, password: undefined, server: undefined })); }}
              error={errors.password}
              required
            />
            {strength && (
              <div className="mt-2">
                <div className="h-1.5 w-full bg-accent rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-300 ${strength.color}`} style={{ width: strength.width }} />
                </div>
                <p className="text-[10px] text-muted-foreground mt-1 uppercase tracking-wider">{strength.label}</p>
              </div>
            )}
          </div>

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