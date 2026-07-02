"use client";

import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Search, RotateCcw } from "lucide-react";

interface Props {
  onFilter: (filters: Record<string, string | number | undefined>) => void;
}

export default function ReviewFilters({ onFilter }: Props) {
  const [rating, setRating] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [source, setSource] = useState("");
  const [search, setSearch] = useState("");

  const applyFilters = () => {
    const f: Record<string, string | number | undefined> = {};
    if (rating) f.rating = parseInt(rating);
    if (sentiment) f.sentiment = sentiment;
    if (source) f.source = source;
    if (search) f.search = search;
    onFilter(f);
  };

  const resetFilters = () => {
    setRating("");
    setSentiment("");
    setSource("");
    setSearch("");
    onFilter({});
  };

  return (
    <Card>
      <CardContent className="p-4 flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[200px]">
          <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Search</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              className="w-full h-9 rounded-md border border-border bg-background pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
              placeholder="Search reviews..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Rating</label>
          <select
            className="h-9 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
            value={rating}
            onChange={(e) => setRating(e.target.value)}
          >
            <option value="">All Ratings</option>
            {[5, 4, 3, 2, 1].map((r) => (
              <option key={r} value={r}>{r} Star{r > 1 ? "s" : ""}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Sentiment</label>
          <select
            className="h-9 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
            value={sentiment}
            onChange={(e) => setSentiment(e.target.value)}
          >
            <option value="">All</option>
            <option value="positive">Positive</option>
            <option value="negative">Negative</option>
            <option value="neutral">Neutral</option>
            <option value="mixed">Mixed</option>
          </select>
        </div>

        <div>
          <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Source</label>
          <select
            className="h-9 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            <option value="">All Sources</option>
            <option value="google">Google</option>
            <option value="manual">Manual</option>
          </select>
        </div>

        <Button size="sm" onClick={applyFilters}>Apply</Button>
        <Button size="sm" variant="ghost" onClick={resetFilters}>
          <RotateCcw className="w-4 h-4" />
        </Button>
      </CardContent>
    </Card>
  );
}
