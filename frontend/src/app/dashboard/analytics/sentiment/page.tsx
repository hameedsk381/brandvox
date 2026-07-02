"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { analyticsAPI } from "@/lib/api";
import { useTenantStore } from "@/stores/tenant-store";
import SentimentBreakdown from "@/components/analytics/sentiment-breakdown";
import EmotionRadar from "@/components/analytics/emotion-radar";
import TrendLine from "@/components/analytics/trend-line";

export default function SentimentDeepDivePage() {
  const pathname = usePathname();
  const currentLocation = useTenantStore((state) => state.currentLocation);

  const { data, isLoading } = useQuery({
    queryKey: ["analytics-sentiment-deep", currentLocation?.id],
    queryFn: () => analyticsAPI.getSentiment(),
    enabled: !!currentLocation?.id,
  });

  const { data: dashboardData } = useQuery({
    queryKey: ["dashboard", currentLocation?.id],
    queryFn: () => analyticsAPI.getDashboard(),
    enabled: !!currentLocation?.id,
  });

  return (
    <div className="max-w-7xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">{currentLocation?.name || "All locations"}</p>
      </div>

      {/* Navigation tabs */}
      <div className="flex border-b border-border gap-6">
        <Link 
          href="/dashboard/analytics" 
          className={`pb-3 text-sm font-medium border-b-2 transition-all ${
            pathname === "/dashboard/analytics" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Overview
        </Link>
        <Link 
          href="/dashboard/analytics/sentiment" 
          className={`pb-3 text-sm font-medium border-b-2 transition-all ${
            pathname === "/dashboard/analytics/sentiment" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Sentiment Deep Dive
        </Link>
        <Link 
          href="/dashboard/analytics/forecasting" 
          className={`pb-3 text-sm font-medium border-b-2 transition-all ${
            pathname === "/dashboard/analytics/forecasting" 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          AI Forecasting
        </Link>
      </div>

      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-foreground">Sentiment Deep Dive</h2>
        <p className="text-sm text-muted-foreground mt-1">Detailed sentiment analysis for {currentLocation?.name || "all locations"}</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-10 h-10 rounded-full border-t-2 border-primary animate-spin" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SentimentBreakdown data={data} detailed />
          <EmotionRadar emotions={data?.emotions} />
          <div className="lg:col-span-2">
            <TrendLine
              data={dashboardData?.rating_trend?.map((p: any) => ({ date: p.date, value: p.avg_rating }))}
              title="Rating Trend"
              dataKey="value"
            />
          </div>
        </div>
      )}
    </div>
  );
}
