"use client";

import { useEffect, useState } from "react";
import { billingAPI } from "@/lib/api";
import { AlertCircle } from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";

export function TrialBanner() {
  const [trialDaysLeft, setTrialDaysLeft] = useState<number | null>(null);
  const [isActive, setIsActive] = useState<boolean>(true);
  const [plan, setPlan] = useState<string>("trial");
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  useEffect(() => {
    if (!isAuthenticated) return;

    billingAPI.getStatus().then((data) => {
      setPlan(data.subscription_plan);
      if (data.subscription_plan !== "trial") {
        setIsActive(true);
        setTrialDaysLeft(null);
        return;
      }
      setIsActive(data.is_trial_active);
      if (data.trial_ends_at) {
        const endsAt = new Date(data.trial_ends_at);
        const now = new Date();
        const diffTime = endsAt.getTime() - now.getTime();
        setTrialDaysLeft(Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
      } else {
        setTrialDaysLeft(null);
      }
    }).catch(console.error);
  }, [isAuthenticated]);

  if (!isAuthenticated || plan !== "trial") return null;

  if (!isActive) {
    return (
      <div className="bg-red-600 text-white px-4 py-3 flex items-center justify-center text-sm font-medium">
        <AlertCircle className="w-4 h-4 mr-2" />
        Your trial has expired. Upgrade to continue using all features.
        <Link href="/dashboard/settings/billing" className="ml-4 underline hover:text-red-100 font-semibold">
          Upgrade Now
        </Link>
      </div>
    );
  }

  if (trialDaysLeft !== null && trialDaysLeft <= 14) {
    return (
      <div className="bg-amber-500 text-white px-4 py-2 flex items-center justify-center text-sm font-medium">
        <AlertCircle className="w-4 h-4 mr-2" />
        You have {trialDaysLeft} day{trialDaysLeft !== 1 ? "s" : ""} left in your trial.
        <Link href="/dashboard/settings/billing" className="ml-4 underline hover:text-amber-100 font-semibold">
          Upgrade Plan
        </Link>
      </div>
    );
  }

  return null;
}