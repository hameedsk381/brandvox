"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";

interface Props {
  data?: { positive: number; negative: number; neutral: number; mixed: number };
}

const COLORS: Record<string, string> = {
  Positive: "#4ade80", // emerald-400
  Negative: "#f87171", // red-400
  Neutral: "#a1a1aa",  // zinc-400
  Mixed: "#facc15",    // yellow-400
};

export default function SentimentDonut({ data }: Props) {
  if (!data) {
    return (
      <Card>
        <CardHeader><CardTitle>Sentiment Distribution</CardTitle></CardHeader>
        <CardContent className="h-72 flex items-center justify-center text-muted-foreground text-sm">
          No sentiment data
        </CardContent>
      </Card>
    );
  }

  const chartData = [
    { name: "Positive", value: data.positive },
    { name: "Negative", value: data.negative },
    { name: "Neutral", value: data.neutral },
    { name: "Mixed", value: data.mixed },
  ].filter((d) => d.value > 0);

  return (
    <Card>
      <CardHeader><CardTitle>Sentiment Distribution</CardTitle></CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={chartData} cx="50%" cy="50%" innerRadius={60} outerRadius={90} paddingAngle={3} dataKey="value">
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={COLORS[entry.name]} stroke="transparent" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 8, color: "hsl(var(--foreground))" }}
                itemStyle={{ color: "hsl(var(--foreground))" }}
                labelStyle={{ color: "hsl(var(--muted-foreground))" }}
              />
              <Legend
                wrapperStyle={{ fontSize: 12, color: "hsl(var(--muted-foreground))" }}
                formatter={(value) => <span style={{ color: "hsl(var(--muted-foreground))" }}>{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
