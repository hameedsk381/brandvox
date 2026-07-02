"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Treemap, ResponsiveContainer, Tooltip } from "recharts";

interface TopicData {
  name: string;
  count: number;
  sentiment_score: number;
}

interface Props {
  data?: TopicData[];
}

export default function TopicAnalysis({ data }: Props) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Topic Analysis</CardTitle></CardHeader>
        <CardContent className="h-72 flex items-center justify-center text-muted-foreground text-sm">No topic data</CardContent>
      </Card>
    );
  }

  const treeData = {
    name: "topics",
    children: data.map((t) => ({
      name: t.name,
      size: t.count,
      sentiment: t.sentiment_score,
    })),
  };

  const CustomizedContent = (props: any) => {
    const { x, y, width, height, name, sentiment } = props;
    if (width < 20 || height < 20) return null;
    const color = sentiment && sentiment >= 0 ? "#22c55e" : sentiment && sentiment < 0 ? "#ef4444" : "#a1a1aa";
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} fill={color} fillOpacity={0.2} stroke="#27272a" strokeWidth={1} rx={4} />
        <text x={x + width / 2} y={y + height / 2} textAnchor="middle" fill="#e4e4e7" fontSize={11} fontWeight={500}>
          {name}
        </text>
      </g>
    );
  };

  return (
    <Card>
      <CardHeader><CardTitle>Topic Analysis</CardTitle></CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <Treemap data={treeData.children} dataKey="size" aspectRatio={4 / 3} stroke="#27272a" content={<CustomizedContent />}>
              <Tooltip
                contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, color: "#f4f4f5" }}
                formatter={(value: number, name: string) => [value, name]}
              />
            </Treemap>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
