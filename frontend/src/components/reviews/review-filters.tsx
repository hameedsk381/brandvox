"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Search, RotateCcw, Save, Bookmark, X } from "lucide-react";
import { useFilterStore } from "@/stores/filter-store";

interface Props {
  onFilter: (filters: Record<string, string | number | undefined>) => void;
}

export default function ReviewFilters({ onFilter }: Props) {
  const {
    currentFilters,
    savedFilters,
    setCurrentFilters,
    saveFilter,
    loadFilter,
    deleteFilter,
  } = useFilterStore();

  const [rating, setRating] = useState(String(currentFilters.rating || ""));
  const [sentiment, setSentiment] = useState(String(currentFilters.sentiment || ""));
  const [source, setSource] = useState(String(currentFilters.source || ""));
  const [search, setSearch] = useState(String(currentFilters.search || ""));
  const [saveName, setSaveName] = useState("");
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  useEffect(() => {
    setRating(String(currentFilters.rating || ""));
    setSentiment(String(currentFilters.sentiment || ""));
    setSource(String(currentFilters.source || ""));
    setSearch(String(currentFilters.search || ""));
  }, [currentFilters]);

  const applyFilters = () => {
    const f: Record<string, string | number | undefined> = {};
    if (rating) f.rating = parseInt(rating);
    if (sentiment) f.sentiment = sentiment;
    if (source) f.source = source;
    if (search) f.search = search;
    setCurrentFilters(f);
    onFilter(f);
  };

  const resetFilters = () => {
    setRating("");
    setSentiment("");
    setSource("");
    setSearch("");
    setCurrentFilters({});
    onFilter({});
  };

  const handleSave = () => {
    if (!saveName.trim()) return;
    saveFilter(saveName.trim());
    setSaveName("");
    setShowSaveDialog(false);
  };

  const handleLoad = (id: string) => {
    loadFilter(id);
  };

  const handleLoadAndApply = (id: string) => {
    const found = savedFilters.find((f) => f.id === id);
    if (found) {
      setRating(String(found.filters.rating || ""));
      setSentiment(String(found.filters.sentiment || ""));
      setSource(String(found.filters.source || ""));
      setSearch(String(found.filters.search || ""));
      loadFilter(id);
      onFilter(found.filters);
    }
  };

  const hasActiveFilters = rating || sentiment || source || search;

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

        {hasActiveFilters && (
          <>
            <div className="w-px h-8 bg-border" />

            <Button size="sm" variant="outline" onClick={() => setShowSaveDialog(true)}>
              <Save className="w-3.5 h-3.5 mr-1" /> Save
            </Button>
          </>
        )}

        {savedFilters.length > 0 && (
          <div className="flex items-center gap-1.5">
            <Bookmark className="w-3.5 h-3.5 text-muted-foreground" />
            {savedFilters.map((sf) => (
              <div key={sf.id} className="flex items-center gap-0.5">
                <button
                  onClick={() => handleLoadAndApply(sf.id)}
                  className="text-xs px-2 py-1 rounded-md border border-border hover:bg-muted/50 transition-colors"
                  title={sf.name}
                >
                  {sf.name}
                </button>
                <button
                  onClick={() => deleteFilter(sf.id)}
                  className="text-muted-foreground hover:text-foreground transition-colors p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {showSaveDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-background rounded-xl border border-border p-6 w-full max-w-sm shadow-2xl">
            <h3 className="font-semibold mb-1 text-foreground">Save current filters</h3>
            <p className="text-xs text-muted-foreground mb-4">Give this view a name so you can return to it later.</p>
            <input
              autoFocus
              className="w-full h-9 rounded-md border border-border bg-background px-3 text-sm text-foreground mb-4 focus:outline-none focus:ring-2 focus:ring-primary/60"
              placeholder="e.g. Negative reviews, Top rated..."
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleSave(); if (e.key === "Escape") setShowSaveDialog(false); }}
            />
            <div className="flex justify-end gap-2">
              <Button size="sm" variant="ghost" onClick={() => setShowSaveDialog(false)}>Cancel</Button>
              <Button size="sm" onClick={handleSave} disabled={!saveName.trim()}>Save</Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
