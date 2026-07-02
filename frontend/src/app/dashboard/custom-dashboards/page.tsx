"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import toast from "react-hot-toast";

const WIDGET_TYPES = [
  { type: "reputation_score", label: "Reputation Score", defaultTitle: "Reputation Score" },
  { type: "avg_rating", label: "Avg Rating", defaultTitle: "Average Rating" },
  { type: "total_reviews", label: "Total Reviews", defaultTitle: "Review Count" },
  { type: "response_rate", label: "Response Rate", defaultTitle: "Response Rate" },
  { type: "sentiment_distribution", label: "Sentiment Distribution", defaultTitle: "Sentiment Breakdown" },
  { type: "rating_trend", label: "Rating Trend", defaultTitle: "Rating Trend (30d)" },
  { type: "recent_reviews", label: "Recent Reviews", defaultTitle: "Recent Reviews" },
  { type: "top_topics", label: "Top Topics", defaultTitle: "Top Topics" },
  { type: "review_volume", label: "Review Volume", defaultTitle: "Review Volume" },
];

interface WidgetConfig {
  type: string;
  title: string;
  width: number;
  height: number;
  x: number;
  y: number;
  settings: Record<string, unknown>;
}

interface DashboardItem {
  id: string;
  name: string;
  description: string | null;
  layout: WidgetConfig[];
  is_default: boolean;
  is_shared: boolean;
  created_at: string;
}

export default function CustomDashboardsPage() {
  const [dashboards, setDashboards] = useState<DashboardItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [editing, setEditing] = useState<DashboardItem | null>(null);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [widgets, setWidgets] = useState<WidgetConfig[]>([]);

  const load = async () => {
    try {
      const res = await api.get("/api/dashboards");
      setDashboards(res.data);
      if (!activeId && res.data.length > 0) setActiveId(res.data[0].id);
    } catch {
      toast.error("Failed to load dashboards");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const activeDashboard = dashboards.find((d) => d.id === activeId) || null;

  const startCreate = () => {
    setEditing(null);
    setName("");
    setDesc("");
    setWidgets([]);
  };

  const startEdit = (d: DashboardItem) => {
    setEditing(d);
    setName(d.name);
    setDesc(d.description || "");
    setWidgets(d.layout);
  };

  const addWidget = (type: string) => {
    const wt = WIDGET_TYPES.find((w) => w.type === type);
    if (!wt) return;
    setWidgets((prev) => [
      ...prev,
      { type, title: wt.defaultTitle, width: 1, height: 1, x: prev.length % 2, y: Math.floor(prev.length / 2), settings: {} },
    ]);
  };

  const removeWidget = (idx: number) => {
    setWidgets((prev) => prev.filter((_, i) => i !== idx));
  };

  const updateWidget = (idx: number, field: string, value: unknown) => {
    setWidgets((prev) => prev.map((w, i) => (i === idx ? { ...w, [field]: value } : w)));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      if (editing) {
        await api.patch(`/api/dashboards/${editing.id}`, { name, description: desc || null, layout: widgets });
        toast.success("Dashboard updated");
      } else {
        await api.post("/api/dashboards", { name, description: desc || null, layout: widgets });
        toast.success("Dashboard created");
      }
      setEditing(null);
      await load();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to save");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this dashboard?")) return;
    try {
      await api.delete(`/api/dashboards/${id}`);
      if (activeId === id) setActiveId(null);
      await load();
      toast.success("Deleted");
    } catch { toast.error("Failed to delete"); }
  };

  const gridClass = (w: WidgetConfig) => {
    const cols: Record<number, string> = { 1: "col-span-1", 2: "col-span-2", 3: "col-span-3" };
    return `${cols[w.width] || "col-span-1"} ${w.height > 1 ? "row-span-2" : ""}`;
  };

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Custom Dashboards</h1>
          <p className="text-sm text-muted-foreground mt-1">Create and manage personalized dashboard layouts</p>
        </div>
        <Button onClick={startCreate}>New Dashboard</Button>
      </div>

      {/* Dashboard selector */}
      {dashboards.length > 0 && !editing && (
        <div className="flex flex-wrap gap-2">
          {dashboards.map((d) => (
            <button key={d.id} onClick={() => setActiveId(d.id)}
              className={`text-sm px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${activeId === d.id ? "bg-primary text-primary-foreground border-primary" : "bg-card text-muted-foreground border-border hover:border-primary/50"}`}>
              {d.name} {d.is_default && "(default)"}
            </button>
          ))}
        </div>
      )}

      {/* Editor form */}
      {(editing || (!editing && name !== undefined && !activeDashboard)) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{editing ? "Edit Dashboard" : "New Dashboard"}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="flex flex-col gap-4">
              <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input label="Description" value={desc} onChange={(e) => setDesc(e.target.value)} />

              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 block">Widgets</label>
                <div className="flex flex-wrap gap-2 mb-3">
                  {WIDGET_TYPES.map((wt) => (
                    <button key={wt.type} type="button" onClick={() => addWidget(wt.type)}
                      className="text-xs px-2.5 py-1 rounded-full border border-border bg-accent/30 text-muted-foreground hover:bg-accent cursor-pointer">
                      + {wt.label}
                    </button>
                  ))}
                </div>
                {widgets.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No widgets yet. Click above to add.</p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {widgets.map((w, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 rounded border border-border bg-accent/10">
                        <span className="text-sm text-foreground min-w-[120px]">{w.title}</span>
                        <select value={w.width} onChange={(e) => updateWidget(i, "width", parseInt(e.target.value))}
                          className="text-xs bg-background border border-border rounded px-1 py-0.5">
                          <option value={1}>1 col</option>
                          <option value={2}>2 col</option>
                          <option value={3}>3 col</option>
                        </select>
                        <input className="flex-1 text-xs bg-transparent border-b border-border px-1 text-foreground" value={w.title} onChange={(e) => updateWidget(i, "title", e.target.value)} placeholder="Title" />
                        <button type="button" onClick={() => removeWidget(i)} className="text-xs text-destructive hover:underline cursor-pointer bg-transparent border-none">Remove</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <Button type="submit">{editing ? "Update" : "Create"}</Button>
                <Button type="button" variant="outline" onClick={() => { setEditing(null); setName(""); setDesc(""); setWidgets([]); }}>Cancel</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Active dashboard preview */}
      {activeDashboard && !editing && (
        <>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-foreground">{activeDashboard.name}</h2>
              {activeDashboard.description && <p className="text-sm text-muted-foreground">{activeDashboard.description}</p>}
            </div>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => startEdit(activeDashboard)}>Edit</Button>
              <Button size="sm" variant="ghost" className="text-destructive" onClick={() => handleDelete(activeDashboard.id)}>Delete</Button>
            </div>
          </div>

          {activeDashboard.layout.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-sm text-muted-foreground">Empty dashboard. Edit to add widgets.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-3 gap-4">
              {activeDashboard.layout.map((w, i) => (
                <div key={i} className={`${gridClass(w)}`}>
                  <Card className="h-full">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">{w.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-xs text-muted-foreground">Widget type: {w.type}</p>
                    </CardContent>
                  </Card>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {!loading && dashboards.length === 0 && !editing && (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-sm text-muted-foreground mb-3">No custom dashboards yet.</p>
            <Button onClick={startCreate}>Create Your First Dashboard</Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}