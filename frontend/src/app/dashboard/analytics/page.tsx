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
import { AnalyticsSkeleton } from "@/components/ui/page-skeleton";

interface RatingPoint {
  date: string;
  avg_rating: number;
  review_count: number;
}

export default function AnalyticsPage() {
  const pathname = usePathname();
  const currentLocation = useTenantStore((state) => state.currentLocation);

  const { data: sentimentData, isLoading } = useQuery({
    queryKey: ["analytics-sentiment", currentLocation?.id],
    queryFn: () => analyticsAPI.getSentiment(),
    enabled: !!currentLocation?.id,
  });

  const { data: dashboardData } = useQuery({
    queryKey: ["dashboard", currentLocation?.id],
    queryFn: () => analyticsAPI.getDashboard(),
    enabled: !!currentLocation?.id,
  });

  if (isLoading) {
    return <AnalyticsSkeleton />;
  }

  const trendData = (dashboardData?.rating_trend as RatingPoint[] | undefined)?.map((p) => ({
    date: p.date,
    value: p.avg_rating,
  }));

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentBreakdown data={sentimentData} />
        <EmotionRadar emotions={sentimentData?.emotions} />
      </div>

      <div className="grid grid-cols-1 gap-6">
        <TrendLine
          data={trendData}
          title="Rating Trend"
          dataKey="value"
        />
      </div>
    </div>
  );
}
