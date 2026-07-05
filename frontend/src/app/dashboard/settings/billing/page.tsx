"use client";

import { useState, useEffect } from "react";
import { billingAPI } from "@/lib/api";
import { Check, CreditCard, ExternalLink, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "@/lib/api";

interface PlanInfo {
  id: string;
  name: string;
  amount: number;
  features: string[];
}

interface BillingStatus {
  subscription_plan: string;
  subscription_status: string;
  trial_ends_at: string | null;
  is_trial_active: boolean;
}

export default function BillingPage() {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [plans, setPlans] = useState<PlanInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [statusData, plansData] = await Promise.all([
          billingAPI.getStatus(),
          api.get("/api/billing/plans").then((r) => r.data),
        ]);
        setStatus(statusData);
        setPlans(plansData);
      } catch {
        toast.error("Failed to load billing data");
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  const handleUpgrade = async (planId: string) => {
    try {
      setIsProcessing(true);
      const res = await billingAPI.checkout(planId);
      const order = res.order;
      const keyId = res.key_id;

      if (res.activated) {
        toast.success(`${planId} plan activated!`);
        const { data: newStatus } = await billingAPI.getStatus();
        setStatus(newStatus);
        return;
      }

      if (keyId && typeof (window as any).Razorpay !== "undefined") {
        const options = {
          key: keyId,
          amount: order.amount,
          currency: order.currency || "USD",
          name: "ReputationOS AI",
          order_id: order.id,
          handler: async (response: any) => {
            toast.success("Payment successful!");
            const { data } = await billingAPI.getStatus();
            setStatus(data);
          },
          prefill: { email: "", contact: "" },
          theme: { color: "#6366f1" },
        };
        const rzp = new (window as any).Razorpay(options);
        rzp.open();
      } else {
        // Payment gateway not configured and server did not activate (production):
        // surface it instead of pretending checkout happened.
        toast.error("Payment gateway is not configured. Contact support to change your plan.");
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Checkout failed");
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const isOnTrial = status?.subscription_plan === "trial";
  const paidPlans = plans.filter((p) => p.id !== "trial" && p.id !== "enterprise");

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Billing & Plans</h1>
        <p className="text-muted-foreground mt-1">Manage your subscription and billing details.</p>
      </div>

      <div className="bg-card rounded-xl border border-border p-6 shadow-sm">
        <h2 className="text-lg font-semibold flex items-center">
          <CreditCard className="w-5 h-5 mr-2 text-primary" />
          Current Plan: {isOnTrial ? "Free Trial" : (status?.subscription_plan || "").toUpperCase()}
        </h2>
        <div className="mt-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-foreground">
              Status: <span className={`capitalize font-medium ${status?.subscription_status === "active" ? "text-emerald-400" : "text-destructive"}`}>
                {status?.subscription_status}
              </span>
            </p>
            {isOnTrial && status?.trial_ends_at && (
              <p className="text-sm text-muted-foreground mt-1">
                Trial ends on {new Date(status.trial_ends_at).toLocaleDateString()}
              </p>
            )}
            {isOnTrial && !status?.is_trial_active && (
              <p className="text-sm text-destructive font-medium mt-1">Your trial has expired</p>
            )}
          </div>
          {!isOnTrial && (
            <button className="flex items-center text-sm font-medium text-primary hover:underline bg-transparent border-none cursor-pointer">
              Manage in Razorpay Portal <ExternalLink className="w-4 h-4 ml-1" />
            </button>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mt-8">
        {paidPlans.map((plan, idx) => {
          const isCurrent = status?.subscription_plan === plan.id;
          return (
            <div key={plan.id} className={`bg-card rounded-xl border${idx === 1 ? "-2 border-primary" : " border-border"} p-6 shadow-sm flex flex-col relative overflow-hidden`}>
              {idx === 1 && (
                <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-xs font-bold px-3 py-1 rounded-bl-lg">
                  RECOMMENDED
                </div>
              )}
              <div className="mb-4">
                <h3 className="text-xl font-bold text-foreground">{plan.name}</h3>
              </div>
              <div className="mb-6">
                <span className="text-3xl font-bold">${plan.amount / 100}</span>
                <span className="text-muted-foreground">/month</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center text-sm">
                    <Check className="w-4 h-4 text-emerald-500 mr-2 shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleUpgrade(plan.id)}
                disabled={isProcessing || isCurrent}
                className={`w-full py-2.5 rounded-lg font-medium transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 ${isCurrent ? "bg-accent text-muted-foreground" : "bg-primary text-primary-foreground hover:bg-primary/90"}`}
              >
                {isProcessing ? "Processing..." : isCurrent ? "Current Plan" : `Upgrade to ${plan.name}`}
              </button>
            </div>
          );
        })}
      </div>

      {/* Load Razorpay script */}
      <script src="https://checkout.razorpay.com/v1/checkout.js" />
    </div>
  );
}