"use client";

import { useEffect, useState } from "react";
import { billingAPI } from "@/lib/api";
import { AlertCircle } from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";

export function TrialBanner() {
  const [trialDaysLeft, setTrialDaysLeft] = useState<number | null>(null);
  const [isActive, setIsActive] = useState<boolean>(true);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());

  useEffect(() => {
    if (!isAuthenticated) return;
    
    billingAPI.getStatus().then((data) => {
      if (data.subscription_status === "active") {
        setIsActive(true);
        setTrialDaysLeft(null);
      } else if (data.trial_ends_at) {
        setIsActive(data.is_trial_active);
        const endsAt = new Date(data.trial_ends_at);
        const now = new Date();
        const diffTime = endsAt.getTime() - now.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        setTrialDaysLeft(diffDays);
      }
    }).catch(console.error);
  }, [isAuthenticated]);

  if (!isAuthenticated || (isActive && trialDaysLeft === null)) {
    return null;
  }

  if (!isActive) {
    return (
      <div className="bg-red-600 text-white px-4 py-3 flex items-center justify-center text-sm font-medium">
        <AlertCircle className="w-4 h-4 mr-2" />
        Your trial has expired. Some features may be disabled.
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
        You have {trialDaysLeft} days left in your trial.
        <Link href="/dashboard/settings/billing" className="ml-4 underline hover:text-amber-100 font-semibold">
          Upgrade Plan
        </Link>
      </div>
    );
  }

  return null;
}
