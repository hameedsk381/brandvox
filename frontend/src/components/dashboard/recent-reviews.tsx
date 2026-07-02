"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Review } from "@/types";
import { RATING_COLORS, SENTIMENT_COLORS } from "@/lib/constants";
import { ArrowRight, Clock } from "lucide-react";

interface Props {
  reviews?: Review[];
}

export default function RecentReviews({ reviews }: Props) {
  if (!reviews || reviews.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Recent Reviews</CardTitle></CardHeader>
        <CardContent className="flex items-center justify-center text-muted-foreground text-sm py-8">
          No recent reviews
        </CardContent>
      </Card>
    );
  }

  const timeAgo = (date: string) => {
    const diff = Date.now() - new Date(date).getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 1) return "just now";
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Reviews</CardTitle>
        <Link href="/dashboard/reviews" className="text-xs text-primary hover:underline flex items-center gap-1">
          View all <ArrowRight className="w-3 h-3" />
        </Link>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {reviews.slice(0, 5).map((review) => (
          <Link
            key={review.id}
            href={`/dashboard/reviews/${review.id}`}
            className="p-3 rounded-md bg-accent/50 border border-border hover:border-accent-foreground/20 transition-colors block"
          >
            <div className="flex items-start justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className={`text-sm font-bold ${RATING_COLORS[review.rating] || "text-muted-foreground"}`}>
                  {"★".repeat(review.rating)}{"☆".repeat(5 - review.rating)}
                </span>
                <span className="text-xs font-medium text-foreground">{review.author_name || "Anonymous"}</span>
              </div>
              <div className="flex items-center gap-1.5">
                {review.sentiment_result && (
                  <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${SENTIMENT_COLORS[review.sentiment_result.sentiment] || ""}`}>
                    {review.sentiment_result.sentiment}
                  </Badge>
                )}
                <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                  <Clock className="w-3 h-3" /> {timeAgo(review.review_date)}
                </span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground line-clamp-2">{review.text}</p>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
