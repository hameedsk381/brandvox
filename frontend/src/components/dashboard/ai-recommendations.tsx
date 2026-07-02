"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Lightbulb, ArrowRight } from "lucide-react";

interface Recommendation {
  id: string;
  type: string;
  title: string;
  description: string;
  target_url?: string;
}

interface Props {
  recommendations?: Recommendation[];
}

const BADGE_VARIANT_MAP: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  reply: "secondary",
  alert: "destructive",
  insight: "outline",
  info: "default",
};

export default function AIRecommendations({ recommendations }: Props) {
  if (!recommendations || recommendations.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>AI Recommendations</CardTitle></CardHeader>
        <CardContent className="flex items-center justify-center text-muted-foreground text-sm py-8">
          No recommendations yet
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>AI Recommendations</CardTitle>
        <Lightbulb className="w-4 h-4 text-amber-400" />
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className="p-3 rounded-md bg-accent/50 border border-border hover:border-accent-foreground/20 transition-colors"
          >
            <div className="flex items-start gap-2 mb-1">
              <Badge variant={BADGE_VARIANT_MAP[rec.type] || "default"}>{rec.type}</Badge>
            </div>
            <p className="text-sm font-medium text-foreground">{rec.title}</p>
            <p className="text-xs text-muted-foreground mt-0.5">{rec.description}</p>
            {rec.target_url && (
              <Link
                href={rec.target_url}
                className="inline-flex items-center gap-1 text-xs text-foreground hover:underline font-medium mt-2"
              >
                Take action <ArrowRight className="w-3 h-3" />
              </Link>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
