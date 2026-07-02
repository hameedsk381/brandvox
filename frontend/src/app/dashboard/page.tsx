"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { analyticsAPI } from "@/lib/api";
import { useTenantStore } from "@/stores/tenant-store";
import StatsGrid from "@/components/dashboard/stats-grid";
import ReputationScoreCard from "@/components/dashboard/reputation-score-card";
import RatingTrendChart from "@/components/dashboard/rating-trend-chart";
import SentimentDonut from "@/components/dashboard/sentiment-donut";
import ReviewVolumeChart from "@/components/dashboard/review-volume-chart";
import AIRecommendations from "@/components/dashboard/ai-recommendations";
import RecentReviews from "@/components/dashboard/recent-reviews";
import { DashboardSkeleton } from "@/components/ui/page-skeleton";

export default function DashboardPage() {
  const currentLocation = useTenantStore((state) => state.currentLocation);

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", currentLocation?.id],
    queryFn: () => analyticsAPI.getDashboard(),
    enabled: !!currentLocation?.id,
  });

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="max-w-7xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground tracking-tight">Reputation Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {currentLocation?.name || "All locations"} &mdash; Overview
        </p>
      </div>

      <StatsGrid data={data} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ReputationScoreCard score={data?.reputation_score} />
        <div className="lg:col-span-2">
          <RatingTrendChart data={data?.rating_trend} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentDonut data={data?.sentiment_distribution} />
        <ReviewVolumeChart data={data?.rating_trend} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AIRecommendations recommendations={data?.ai_recommendations} />
        <RecentReviews reviews={data?.recent_reviews} />
      </div>
    </div>
  );
}
