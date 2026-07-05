"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

// Compliance note: every rating gets the SAME next step. Google's review
// policies and the FTC's review rule prohibit "review gating" — selectively
// steering happy customers to Google while diverting unhappy ones to a
// private form. Do not reintroduce rating-based branching here.
function FunnelContent() {
  const searchParams = useSearchParams();
  const contactId = searchParams.get("contact_id");
  const businessName = searchParams.get("business") || "our business";
  const reviewUrl = searchParams.get("review_url");
  const [step, setStep] = useState<"rating" | "share" | "done">("rating");
  const [rating, setRating] = useState<number | null>(null);
  const [feedbackText, setFeedbackText] = useState("");

  const handleRating = (value: number) => {
    setRating(value);
    setStep("share");
  };

  const submitFeedback = async (text: string) => {
    if (contactId) {
      try {
        await api.post("/api/campaigns/funnel/feedback", {
          contact_id: contactId,
          feedback_text: rating != null ? `Rated ${rating}/5. ${text}` : text,
        });
      } catch {}
    }
  };

  const handleSubmitFeedback = async () => {
    await submitFeedback(feedbackText);
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

          {step === "share" && (
            <div className="flex flex-col items-center gap-4 w-full text-center">
              <p className="text-sm text-muted-foreground">
                Thanks for rating us! We&apos;d love to hear more about your experience.
              </p>

              {reviewUrl && (
                <a
                  href={reviewUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={() => {
                    submitFeedback("Opened Google review link");
                    setStep("done");
                  }}
                >
                  <Button className="text-lg px-8 py-4">Share on Google</Button>
                </a>
              )}

              <div className="flex flex-col items-center gap-3 w-full">
                <p className="text-xs text-muted-foreground">
                  {reviewUrl ? "You can also send us a note directly:" : "Tell us about your experience:"}
                </p>
                <textarea
                  className="w-full min-h-[120px] bg-background border border-border rounded-lg p-3 text-sm"
                  placeholder="Your feedback helps us get better..."
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                />
                <Button onClick={handleSubmitFeedback} disabled={!feedbackText.trim()}>
                  Submit Feedback
                </Button>
              </div>
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
