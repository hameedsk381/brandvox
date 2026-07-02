"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import toast from "react-hot-toast";

const EVENT_TYPES = [
  "review.created", "reply.posted", "crisis.detected",
  "sync.completed", "report.generated", "score.changed",
];

interface Endpoint {
  id: string;
  name: string;
  url: string;
  event_types: string[];
  is_active: boolean;
  last_success_at: string | null;
  last_failure_at: string | null;
  failure_count: number;
  created_at: string;
}

export default function WebhooksPage() {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>(["review.created"]);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    try {
      const res = await api.get("/api/webhooks/endpoints");
      setEndpoints(res.data);
    } catch {
      toast.error("Failed to load webhooks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const toggleEvent = (et: string) => {
    setSelectedEvents((prev) =>
      prev.includes(et) ? prev.filter((e) => e !== et) : [...prev, et]
    );
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !url.trim() || selectedEvents.length === 0) return;
    try {
      await api.post("/api/webhooks/endpoints", { name, url, event_types: selectedEvents });
      toast.success("Webhook created");
      setName(""); setUrl(""); setSelectedEvents(["review.created"]);
      setShowForm(false);
      await load();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to create webhook");
    }
  };

  const handleToggle = async (ep: Endpoint) => {
    try {
      await api.patch(`/api/webhooks/endpoints/${ep.id}`, { is_active: !ep.is_active });
      await load();
    } catch { toast.error("Failed to toggle"); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this webhook endpoint?")) return;
    try {
      await api.delete(`/api/webhooks/endpoints/${id}`);
      await load();
      toast.success("Deleted");
    } catch { toast.error("Failed to delete"); }
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Webhooks</h1>
        <p className="text-sm text-muted-foreground mt-1">Send real-time events to external services</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Endpoints</CardTitle>
              <CardDescription>{endpoints.length} configured</CardDescription>
            </div>
            <Button size="sm" onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "Add Endpoint"}</Button>
          </div>
        </CardHeader>
        <CardContent>
          {showForm && (
            <form onSubmit={handleCreate} className="flex flex-col gap-4 mb-6 p-4 bg-accent/20 rounded-lg border border-border">
              <Input label="Name" placeholder="e.g. Slack Notifications" value={name} onChange={(e) => setName(e.target.value)} required />
              <Input label="Webhook URL" type="url" placeholder="https://hooks.example.com/..." value={url} onChange={(e) => setUrl(e.target.value)} required />
              <div>
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 block">Event Types</label>
                <div className="flex flex-wrap gap-2">
                  {EVENT_TYPES.map((et) => (
                    <button key={et} type="button" onClick={() => toggleEvent(et)}
                      className={`text-xs px-2.5 py-1 rounded-full border transition-all cursor-pointer ${selectedEvents.includes(et) ? "bg-primary text-primary-foreground border-primary" : "bg-background text-muted-foreground border-border hover:border-primary/50"}`}>
                      {et}
                    </button>
                  ))}
                </div>
              </div>
              <Button type="submit" disabled={!name.trim() || !url.trim() || selectedEvents.length === 0}>Create</Button>
            </form>
          )}

          {loading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : endpoints.length === 0 ? (
            <p className="text-sm text-muted-foreground">No webhooks configured.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {endpoints.map((ep) => (
                <div key={ep.id} className="p-4 rounded-lg border border-border bg-accent/10">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className="text-sm font-medium text-foreground">{ep.name}</span>
                      <span className={`ml-2 text-[10px] px-1.5 py-0.5 rounded-full font-medium ${ep.is_active ? "bg-emerald-500/10 text-emerald-400" : "bg-muted text-muted-foreground"}`}>
                        {ep.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button size="sm" variant="ghost" onClick={() => handleToggle(ep)}>{ep.is_active ? "Pause" : "Activate"}</Button>
                      <Button size="sm" variant="ghost" className="text-destructive" onClick={() => handleDelete(ep.id)}>Delete</Button>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground font-mono truncate">{ep.url}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {ep.event_types.map((et) => (
                      <span key={et} className="text-[10px] px-1.5 py-0.5 rounded bg-accent text-muted-foreground">{et}</span>
                    ))}
                  </div>
                  <div className="flex gap-4 mt-2 text-[10px] text-muted-foreground">
                    {ep.last_success_at && <span>Last success: {new Date(ep.last_success_at).toLocaleString()}</span>}
                    {ep.failure_count > 0 && <span className="text-destructive">{ep.failure_count} failure{ep.failure_count > 1 ? "s" : ""}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}