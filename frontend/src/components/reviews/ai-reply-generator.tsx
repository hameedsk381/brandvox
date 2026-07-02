"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useGenerateAIReply, useApproveReply, useRejectReply } from "@/hooks/use-reviews";
import { ReviewReply } from "@/types";
import { Sparkles, Check, X } from "lucide-react";

interface Props {
  reviewId: string;
  reply?: ReviewReply;
}

const REPLY_BADGE_VARIANTS: Record<string, "default" | "outline" | "secondary" | "destructive"> = {
  approved: "secondary",
  draft: "outline",
  posted: "default",
  rejected: "destructive",
  replaced: "outline",
};

export default function AIReplyGenerator({ reviewId, reply }: Props) {
  const generateReply = useGenerateAIReply();
  const approveReply = useApproveReply();
  const rejectReply = useRejectReply();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <Sparkles className="w-4 h-4 text-primary" /> AI Reply Generator
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <Button onClick={() => generateReply.mutate(reviewId)} loading={generateReply.isPending} variant="outline" size="sm" className="w-fit">
          <Sparkles className="w-4 h-4 mr-1.5" /> Generate
        </Button>

        {reply && (
          <div className="p-3 rounded-lg bg-muted/50 border border-border">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={REPLY_BADGE_VARIANTS[reply.status] || "outline"} className="text-[10px]">
                {reply.status}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">{reply.content}</p>
            {reply.status === "draft" && (
              <div className="flex items-center gap-2 mt-3">
                <Button size="sm" variant="outline" onClick={() => approveReply.mutate(reply.id)} loading={approveReply.isPending}>
                  <Check className="w-3.5 h-3.5 mr-1" /> Approve
                </Button>
                <Button size="sm" variant="ghost" onClick={() => rejectReply.mutate(reply.id)} loading={rejectReply.isPending} className="text-rose-400">
                  <X className="w-3.5 h-3.5 mr-1" /> Reject
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
