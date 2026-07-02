"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useReviews, useApproveReply, useRejectReply } from "@/hooks/use-reviews";
import { Review, ReviewReply } from "@/types";
import { Check, X, MessageSquare } from "lucide-react";

export default function ApprovalQueue() {
  const { data } = useReviews({ reply_status: "draft" });
  const approveReply = useApproveReply();
  const rejectReply = useRejectReply();

  const reviews: Review[] = data?.items || data?.reviews || [];
  const pendingReplies = reviews.filter((r) =>
    r.replies?.some((rep) => rep.status === "draft")
  );

  if (pendingReplies.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle className="text-sm">Approval Queue</CardTitle></CardHeader>
        <CardContent className="text-xs text-muted-foreground text-center py-6">
          No pending replies
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-amber-400" />
          Approval Queue ({pendingReplies.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {pendingReplies.map((review) => {
          const draft = review.replies?.find((r: ReviewReply) => r.status === "draft");
          return (
            <div key={review.id} className="p-3 rounded-lg bg-muted/50 border border-border">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold text-muted-foreground">{review.author_name}</span>
                <Badge variant="outline" className="text-[10px]">{review.rating}/5</Badge>
              </div>
              <p className="text-xs text-muted-foreground line-clamp-1 mb-2">{review.text}</p>
              {draft && (
                <>
                  <div className="p-2 rounded bg-background border border-border mb-2">
                    <p className="text-xs text-muted-foreground italic">"{draft.content}"</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => approveReply.mutate(draft.id)} loading={approveReply.isPending}>
                      <Check className="w-3.5 h-3.5 mr-1" /> Approve
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => rejectReply.mutate(draft.id)} loading={rejectReply.isPending} className="text-rose-400">
                      <X className="w-3.5 h-3.5 mr-1" /> Reject
                    </Button>
                  </div>
                </>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
