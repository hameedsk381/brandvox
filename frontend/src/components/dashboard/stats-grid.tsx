"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Star, MessageSquare, Clock, Smile } from "lucide-react";

interface StatsGridProps {
  data?: {
    reputation_score?: number;
    avg_rating?: number;
    total_reviews?: number;
    response_rate?: number;
    sentiment_score?: number;
    review_growth?: number;
  };
}

export default function StatsGrid({ data }: StatsGridProps) {
  const stats = [
    {
      label: "Reputation Score",
      value: data?.reputation_score != null ? `${Math.round(data.reputation_score)}/100` : "--",
      icon: Star,
      color: "text-amber-400",
    },
    {
      label: "Average Rating",
      value: data?.avg_rating != null ? `${data.avg_rating.toFixed(1)} ★` : "--",
      icon: Star,
      color: "text-emerald-400",
    },
    {
      label: "Total Reviews",
      value: data?.total_reviews != null ? data.total_reviews.toLocaleString() : "--",
      icon: MessageSquare,
      color: "text-blue-400",
    },
    {
      label: "Response Rate",
      value: data?.response_rate != null ? `${(data.response_rate * 100).toFixed(0)}%` : "--",
      icon: Clock,
      color: "text-violet-400",
    },
    {
      label: "Sentiment Score",
      value: data?.sentiment_score != null ? data.sentiment_score.toFixed(2) : "--",
      icon: Smile,
      color: "text-cyan-400",
    },
    {
      label: "Review Growth",
      value: data?.review_growth != null ? `${data.review_growth > 0 ? "+" : ""}${data.review_growth}%` : "--",
      icon: data?.review_growth != null && data.review_growth >= 0 ? TrendingUp : TrendingDown,
      color: data?.review_growth != null && data.review_growth >= 0 ? "text-emerald-400" : "text-rose-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.label} className="overflow-hidden">
            <CardContent className="p-4 flex flex-col gap-1.5">
              <div className="flex items-center gap-2">
                <Icon className={`w-4 h-4 ${stat.color}`} />
                <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                  {stat.label}
                </span>
              </div>
              <span className="text-xl font-semibold text-foreground tracking-tight">{stat.value}</span>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
