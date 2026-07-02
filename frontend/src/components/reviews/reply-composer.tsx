"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { useSubmitReply } from "@/hooks/use-reviews";
import { Send } from "lucide-react";

interface Props {
  reviewId: string;
}

export default function ReplyComposer({ reviewId }: Props) {
  const [content, setContent] = useState("");
  const submitReply = useSubmitReply();

  const handleSubmit = () => {
    if (content.trim()) {
      submitReply.mutate({ reviewId, data: { content } });
      setContent("");
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <textarea
        className="w-full min-h-[100px] rounded-lg border border-border bg-background p-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/60 resize-y"
        placeholder="Write a reply..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
      />
      <Button onClick={handleSubmit} loading={submitReply.isPending} className="w-fit" size="sm">
        <Send className="w-4 h-4 mr-1.5" /> Send Reply
      </Button>
    </div>
  );
}
