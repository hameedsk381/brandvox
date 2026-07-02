"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface Props {
  data?: { date: string; value: number; label?: string }[];
  title?: string;
  dataKey?: string;
  color?: string;
}

export default function TrendLine({ data, title = "Trend", dataKey = "value", color = "#6366f1" }: Props) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
        <CardContent className="h-72 flex items-center justify-center text-muted-foreground text-sm">No trend data</CardContent>
      </Card>
    );
  }

  const formatted = data.map((d) => ({
    ...d,
    date: new Date(d.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
  }));

  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={formatted}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="date" tick={{ fill: "#a1a1aa", fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: "#a1a1aa", fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, color: "#f4f4f5" }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: "#a1a1aa" }} />
              <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={{ fill: color, r: 3 }} name={title} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
