"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";

interface Props {
  score?: number;
}

export default function ReputationScoreCard({ score }: Props) {
  const s = score ?? 0;
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (s / 100) * circumference;

  const getColor = () => {
    if (s >= 80) return "#22c55e";
    if (s >= 60) return "#eab308";
    if (s >= 40) return "#f97316";
    return "#ef4444";
  };

  return (
    <Card>
      <CardContent className="p-6 flex flex-col items-center">
        <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-4">
          Reputation Score
        </h3>
        <div className="relative flex items-center justify-center">
          <svg width="180" height="180" className="-rotate-90">
            <circle cx="90" cy="90" r={radius} fill="none" stroke="currentColor" className="text-muted/20" strokeWidth="10" />
            <circle
              cx="90"
              cy="90"
              r={radius}
              fill="none"
              stroke={getColor()}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            <span className="text-4xl font-semibold text-foreground tracking-tight">{Math.round(s)}</span>
            <span className="text-xs text-muted-foreground">/ 100</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          {s >= 80 ? "Excellent" : s >= 60 ? "Good" : s >= 40 ? "Needs Work" : "Critical"}
        </p>
      </CardContent>
    </Card>
  );
}
