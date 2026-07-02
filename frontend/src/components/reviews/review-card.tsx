"use client";

import React from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Review } from "@/types";
import { SENTIMENT_COLORS, RATING_COLORS } from "@/lib/constants";
import { Clock, MessageSquare } from "lucide-react";

interface Props {
  review: Review;
}

export default function ReviewCard({ review }: Props) {
  const timeAgo = (date: string) => {
    const diff = Date.now() - new Date(date).getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 1) return "just now";
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const hasReply = review.replies && review.replies.length > 0;
  const replyStatus = review.replies?.[review.replies.length - 1]?.status;

  return (
    <Link href={`/dashboard/reviews/${review.id}`}>
      <Card className="hover:border-border/60 transition-all cursor-pointer">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className={`text-lg font-bold ${RATING_COLORS[review.rating] || "text-muted-foreground"}`}>
                {"★".repeat(review.rating)}{"☆".repeat(5 - review.rating)}
              </span>
              <span className="text-sm font-semibold text-foreground">{review.author_name || "Anonymous"}</span>
            </div>
            <div className="flex items-center gap-2">
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
          <p className="text-sm text-muted-foreground line-clamp-2 mb-2">{review.text}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="outline" className="text-[10px] border-border">{review.source}</Badge>
            {hasReply && (
              <span className={`flex items-center gap-1 ${replyStatus === "approved" ? "text-emerald-400" : replyStatus === "draft" ? "text-amber-400" : "text-muted-foreground"}`}>
                <MessageSquare className="w-3 h-3" /> {replyStatus}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
