"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useReview, useGenerateAIReply, useSubmitReply } from "@/hooks/use-reviews";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SENTIMENT_COLORS, RATING_COLORS } from "@/lib/constants";
import { ArrowLeft, Sparkles, Bot, User } from "lucide-react";
import Link from "next/link";

export default function ReviewDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { data: review, isLoading } = useReview(id);
  const generateReply = useGenerateAIReply();
  const submitReply = useSubmitReply();
  const [manualContent, setManualContent] = useState("");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 rounded-full border-t-2 border-primary animate-spin" />
      </div>
    );
  }

  if (!review) {
    return <div className="text-muted-foreground text-center py-16">Review not found</div>;
  }

  const latestReply = review.replies?.[review.replies?.length - 1];

  const handleGenerateAI = () => generateReply.mutate(id);
  const handleSubmitReply = () => {
    if (manualContent.trim()) {
      submitReply.mutate({ reviewId: id, data: { content: manualContent } });
      setManualContent("");
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <Link href="/dashboard/reviews" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back to Reviews
      </Link>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            <CardTitle>Review by {review.author_name || "Anonymous"}</CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              {new Date(review.review_date).toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
              &nbsp;&middot;&nbsp;{review.source}
            </p>
          </div>
          <span className={`text-2xl font-black ${RATING_COLORS[review.rating] || "text-muted-foreground"}`}>
            {review.rating}/5
          </span>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground leading-relaxed">{review.text}</p>

          {review.sentiment_result && (
            <div className="flex items-center gap-3">
              <Badge variant="outline" className={SENTIMENT_COLORS[review.sentiment_result.sentiment]}>
                {review.sentiment_result.sentiment}
              </Badge>
              <span className="text-xs text-muted-foreground">
                Confidence: {((review.sentiment_result.confidence || 0) * 100).toFixed(0)}%
              </span>
              {review.sentiment_result.emotions?.map((e: string) => (
                <Badge key={e} variant="secondary" className="text-[10px]">{e}</Badge>
              ))}
            </div>
          )}

          {review.topic_results && review.topic_results.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {review.topic_results.map((t: any, i: number) => (
                <Badge key={i} variant="outline" className="text-[10px] border-border text-muted-foreground">
                  {t.topic}{t.sub_topic ? ` / ${t.sub_topic}` : ""}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-primary" /> AI Reply Generator
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Button onClick={handleGenerateAI} loading={generateReply.isPending} variant="outline" className="w-fit">
            <Sparkles className="w-4 h-4 mr-2" /> Generate AI Reply
          </Button>

          {latestReply?.generated_by === "ai" && (
            <div className="p-4 rounded-lg bg-muted/50 border border-border">
              <div className="flex items-center gap-2 mb-2">
                <Bot className="w-4 h-4 text-primary" />
                <span className="text-xs font-semibold text-muted-foreground">AI Generated</span>
                <Badge variant={latestReply.status === "approved" ? "success" : "warning"} className="ml-auto text-[10px]">
                  {latestReply.status}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{latestReply.content}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-4 h-4 text-muted-foreground" /> Manual Reply
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <textarea
            className="w-full min-h-[120px] rounded-lg border border-border bg-background p-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/60 resize-y"
            placeholder="Write your reply..."
            value={manualContent}
            onChange={(e) => setManualContent(e.target.value)}
          />
          <div className="flex items-center gap-3">
            <Button onClick={handleSubmitReply} loading={submitReply.isPending}>
              Submit Reply
            </Button>
            {latestReply?.status === "draft" && (
              <Button variant="ghost" onClick={() => submitReply.mutate({ reviewId: id, data: { content: latestReply.content } })}>
                Submit AI Draft
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
