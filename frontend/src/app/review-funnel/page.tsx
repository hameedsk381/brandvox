"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

function FunnelContent() {
  const searchParams = useSearchParams();
  const contactId = searchParams.get("contact_id");
  const businessName = searchParams.get("business") || "our business";
  const [step, setStep] = useState<"rating" | "happy" | "feedback" | "done">("rating");
  const [feedbackText, setFeedbackText] = useState("");

  const handleRating = async (rating: number) => {
    if (rating >= 4) {
      setStep("happy");
    } else {
      setStep("feedback");
    }
  };

  const handleSubmitFeedback = async () => {
    if (contactId) {
      try {
        await api.post("/api/campaigns/funnel/feedback", {
          contact_id: contactId,
          feedback_text: feedbackText,
        });
      } catch {}
    }
    setStep("done");
  };

  if (step === "done") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="max-w-md w-full text-center">
          <CardContent className="p-8">
            <h2 className="text-xl font-bold text-foreground mb-2">Thank You!</h2>
            <p className="text-sm text-muted-foreground">Your feedback has been recorded.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center">
          <CardTitle className="text-xl">How was your experience at {businessName}?</CardTitle>
          <CardDescription>Your feedback helps us improve</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-6">
          {step === "rating" && (
            <div className="flex flex-col items-center gap-4">
              <p className="text-sm text-muted-foreground">Tap a star to rate your experience</p>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => handleRating(star)}
                    className="text-4xl text-muted-foreground hover:text-amber-400 transition-colors focus:outline-none"
                  >
                    ★
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === "happy" && (
            <div className="flex flex-col items-center gap-4 text-center">
              <p className="text-emerald-400 text-lg">We're glad you had a great experience!</p>
              <p className="text-sm text-muted-foreground">Would you mind sharing your feedback on Google?</p>
              <a
                href={searchParams.get("review_url") || "https://g.page/r/CvFnP4d4M2r7EBM/review"}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => {
                  if (contactId) {
                    api.post("/api/campaigns/funnel/feedback", {
                      contact_id: contactId,
                      feedback_text: "Left a Google review",
                    }).catch(() => {});
                  }
                  setStep("done");
                }}
              >
                <Button className="text-lg px-8 py-4">Leave a Google Review</Button>
              </a>
            </div>
          )}

          {step === "feedback" && (
            <div className="flex flex-col items-center gap-4 w-full">
              <p className="text-sm text-muted-foreground">We're sorry your experience wasn't great. Tell us how we can improve.</p>
              <textarea
                className="w-full min-h-[120px] bg-background border border-border rounded-lg p-3 text-sm"
                placeholder="Your feedback helps us get better..."
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
              />
              <Button onClick={handleSubmitFeedback} disabled={!feedbackText.trim()}>Submit Feedback</Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ReviewFunnelPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <Card className="max-w-md w-full text-center">
          <CardContent className="p-8">
            <p className="text-sm text-muted-foreground">Loading...</p>
          </CardContent>
        </Card>
      </div>
    }>
      <FunnelContent />
    </Suspense>
  );
}