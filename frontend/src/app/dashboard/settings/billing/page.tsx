"use client";

import { useState, useEffect } from "react";
import { billingAPI } from "@/lib/api";
import { Check, CreditCard, ExternalLink, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

export default function BillingPage() {
  const [status, setStatus] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const data = await billingAPI.getStatus();
      setStatus(data);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    try {
      setIsProcessing(true);
      const res = await billingAPI.checkout(planId);
      // In a real Razorpay integration, we'd initialize the Razorpay checkout script here
      // For now we just show a success message or mock redirect
      toast.success(`Razorpay checkout initiated for ${planId} plan (Mock)`);
      console.log("Order details:", res.order);
      
      // Simulate successful payment webhook after 2 seconds
      setTimeout(() => {
        toast.success("Payment successful!");
        fetchStatus();
      }, 2000);
      
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to start checkout");
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

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Billing & Plans</h1>
        <p className="text-muted-foreground mt-1">Manage your subscription and billing details.</p>
      </div>

      <div className="bg-card rounded-xl border border-border p-6 shadow-sm">
        <h2 className="text-lg font-semibold flex items-center">
          <CreditCard className="w-5 h-5 mr-2 text-primary" />
          Current Plan: {status?.subscription_plan === "trial" ? "Free Trial" : status?.subscription_plan?.toUpperCase()}
        </h2>
        <div className="mt-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-foreground">
              Status: <span className="capitalize font-medium text-emerald-600">{status?.subscription_status}</span>
            </p>
            {status?.trial_ends_at && status.subscription_plan === "trial" && (
              <p className="text-sm text-muted-foreground mt-1">
                Trial ends on {new Date(status.trial_ends_at).toLocaleDateString()}
              </p>
            )}
          </div>
          {status?.subscription_plan !== "trial" && (
            <button className="flex items-center text-sm font-medium text-primary hover:underline">
              Manage in Razorpay Portal <ExternalLink className="w-4 h-4 ml-1" />
            </button>
          )}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mt-8">
        {/* Starter Plan */}
        <div className="bg-card rounded-xl border border-border p-6 shadow-sm flex flex-col relative overflow-hidden">
          <div className="mb-4">
            <h3 className="text-xl font-bold text-foreground">Starter</h3>
            <p className="text-muted-foreground text-sm mt-1">For small businesses starting out.</p>
          </div>
          <div className="mb-6">
            <span className="text-3xl font-bold">$19</span>
            <span className="text-muted-foreground">/month</span>
          </div>
          <ul className="space-y-3 mb-8 flex-1">
            <li className="flex items-center text-sm"><Check className="w-4 h-4 text-emerald-500 mr-2 shrink-0" /> Up to 3 locations</li>
            <li className="flex items-center text-sm"><Check className="w-4 h-4 text-emerald-500 mr-2 shrink-0" /> Standard AI replies</li>
            <li className="flex items-center text-sm"><Check className="w-4 h-4 text-emerald-500 mr-2 shrink-0" /> Basic reporting</li>
          </ul>
          <button 
            onClick={() => handleUpgrade("starter")}
            disabled={isProcessing || status?.subscription_plan === "starter"}
            className="w-full py-2.5 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
            {status?.subscription_plan === "starter" ? "Current Plan" : "Upgrade to Starter"}
          </button>
        </div>

        {/* Pro Plan */}
        <div className="bg-card rounded-xl border-2 border-primary p-6 shadow-md flex flex-col relative overflow-hidden">
          <div className="absolute top-0 right-0 bg-primary text-primary-foreground text-xs font-bold px-3 py-1 rounded-bl-lg">
            RECOMMENDED
          </div>
          <div className="mb-4">
            <h3 className="text-xl font-bold text-foreground">Pro</h3>
            <p className="text-muted-foreground text-sm mt-1">For growing agencies and brands.</p>
          </div>
          <div className="mb-6">
            <span className="text-3xl font-bold">$49</span>
            <span className="text-muted-foreground">/month</span>
          </div>
          <ul className="space-y-3 mb-8 flex-1">
            <li className="flex items-center text-sm"><Check className="w-4 h-4 text-emerald-500 mr-2 shrink-0" /> Unlimited locations</li>
            <li className="flex items-center text-sm"><Check className="w-4 h-4 text-emerald-500 mr-2 shrink-0" /> Advanced AI Copilot</li>
            <li className="flex items-center text-sm"><Check className="w-4 h-4 text-emerald-500 mr-2 shrink-0" /> Competitor & Forecasting</li>
            <li className="flex items-center text-sm"><Check className="w-4 h-4 text-emerald-500 mr-2 shrink-0" /> Custom branding</li>
          </ul>
          <button 
            onClick={() => handleUpgrade("pro")}
            disabled={isProcessing || status?.subscription_plan === "pro"}
            className="w-full py-2.5 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
          >
             {status?.subscription_plan === "pro" ? "Current Plan" : "Upgrade to Pro"}
          </button>
        </div>
      </div>
    </div>
  );
}
