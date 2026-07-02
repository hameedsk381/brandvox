"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface Props {
  data?: { sentiment_distribution?: { positive: number; negative: number; neutral: number; mixed: number } };
  detailed?: boolean;
}

const COLORS: Record<string, string> = {
  positive: "#4ade80", // emerald-400
  negative: "#f87171", // red-400
  neutral: "#a1a1aa",  // zinc-400
  mixed: "#facc15",    // yellow-400
};

export default function SentimentBreakdown({ data, detailed }: Props) {
  const dist = data?.sentiment_distribution;
  if (!dist) {
    return (
      <Card>
        <CardHeader><CardTitle>Sentiment Breakdown</CardTitle></CardHeader>
        <CardContent className="h-72 flex items-center justify-center text-muted-foreground text-sm">No data</CardContent>
      </Card>
    );
  }

  const chartData = Object.entries(dist).map(([name, value]) => ({ name, value }));
  const total = chartData.reduce((sum, d) => sum + d.value, 0);

  return (
    <Card>
      <CardHeader><CardTitle>Sentiment Breakdown</CardTitle></CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" horizontal={false} />
              <XAxis type="number" tick={{ fill: "#a1a1aa", fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 11 }} tickLine={false} axisLine={false} width={70} />
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, color: "#f4f4f5" }}
                itemStyle={{ color: "#f4f4f5" }}
                labelStyle={{ color: "#a1a1aa" }}
                formatter={(value: number) => [`${value}${total > 0 ? ` (${((value / total) * 100).toFixed(1)}%)` : ""}`, "Count"]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={COLORS[entry.name] || "#a1a1aa"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
