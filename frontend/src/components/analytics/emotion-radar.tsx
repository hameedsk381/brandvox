"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip } from "recharts";

interface Props {
  emotions?: Record<string, number>;
}

export default function EmotionRadar({ emotions }: Props) {
  if (!emotions || Object.keys(emotions).length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Emotion Radar</CardTitle></CardHeader>
        <CardContent className="h-72 flex items-center justify-center text-muted-foreground text-sm">No emotion data</CardContent>
      </Card>
    );
  }

  const chartData = Object.entries(emotions).map(([emotion, count]) => ({
    emotion,
    count,
  }));

  return (
    <Card>
      <CardHeader><CardTitle>Emotion Radar</CardTitle></CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartData}>
              <PolarGrid stroke="#27272a" />
              <PolarAngleAxis dataKey="emotion" tick={{ fill: "#a1a1aa", fontSize: 10 }} />
              <PolarRadiusAxis tick={false} axisLine={false} />
              <Radar dataKey="count" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} strokeWidth={2} />
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, color: "#f4f4f5" }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
