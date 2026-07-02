"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import toast from "react-hot-toast";

interface FunnelData {
  total_customers: number; reviewed: number; chatted: number;
  ticketed: number; positive_sentiment: number; repeat_visitors: number;
  segment_breakdown: Record<string, number>; total_revenue: number;
}

interface Insight {
  type: string; severity: string; title: string;
  detail: string; recommendation: string;
}

interface Profile {
  id: string; email: string | null; name: string | null;
  phone: string | null; total_orders: number; total_spent: number;
  lifetime_value: number; segment: string | null;
  churn_risk_score: number; last_activity_at: string | null; tags: string[];
}

const SEGMENT_COLORS: Record<string, string> = {
  promoter: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  high_value: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  at_risk: "text-rose-400 bg-rose-500/10 border-rose-500/20",
  detractor: "text-orange-400 bg-orange-500/10 border-orange-500/20",
  new: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  lost: "text-muted-foreground bg-zinc-500/10 border-zinc-500/20",
};

export default function CustomerJourneyPage() {
  const [funnel, setFunnel] = useState<FunnelData | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<string>("funnel");
  const [segmentFilter, setSegmentFilter] = useState<string>("");
  const [csvData, setCsvData] = useState("");
  const [importType, setImportType] = useState<string>("crm");
  const [showImport, setShowImport] = useState(false);

  const loadData = async () => {
    try {
      const [fRes, pRes] = await Promise.all([
        api.get("/api/customer-journey/funnel?days=90"),
        api.get(`/api/customer-journey/profiles${segmentFilter ? `?segment=${segmentFilter}` : ""}`),
      ]);
      setFunnel(fRes.data);
      setProfiles(pRes.data);
    } catch { toast.error("Failed to load data"); }
    finally { setLoading(false); }
  };

  useEffect(() => { loadData(); }, [segmentFilter]);

  const handleAnalyze = async () => {
    try {
      const res = await api.post("/api/customer-journey/analyze");
      setInsights(res.data.insights || []);
      toast.success("Analysis complete");
      setTab("insights");
    } catch { toast.error("Failed to analyze"); }
  };

  const handleSegment = async () => {
    try {
      const res = await api.post("/api/customer-journey/segment");
      toast.success(`Segmented ${res.data.total_profiles} profiles`);
      await loadData();
    } catch { toast.error("Failed to segment"); }
  };

  const handleImport = async () => {
    if (!csvData.trim()) return;
    try {
      const endpoint = importType === "crm" ? "/api/customer-journey/import/crm"
        : importType === "orders" ? "/api/customer-journey/import/orders"
        : "/api/customer-journey/import/feedback";
      const res = await api.post(endpoint, { csv_data: csvData });
      toast.success(`Imported ${res.data.imported} records`);
      setCsvData("");
      setShowImport(false);
      await loadData();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Import failed");
    }
  };

  if (loading) return <div className="p-8 text-muted-foreground">Loading...</div>;

  const severityColor = (s: string) =>
    s === "high" ? "text-rose-400 border-rose-400/30" :
    s === "medium" ? "text-amber-400 border-amber-400/30" :
    "text-blue-400 border-blue-400/30";

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Customer Intelligence</h1>
          <p className="text-sm text-muted-foreground mt-1">Unified customer view — profiles, segments, insights, and data import</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={handleSegment}>Run Segmentation</Button>
          <Button size="sm" variant="outline" onClick={handleAnalyze}>AI Analysis</Button>
          <Button size="sm" onClick={() => setShowImport(!showImport)}>{showImport ? "Cancel" : "Import Data"}</Button>
        </div>
      </div>

      {showImport && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Import Data</CardTitle>
            <CardDescription>Paste CSV data to import customer records</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mb-3">
              {[
                { value: "crm", label: "CRM Contacts", cols: "email,name,phone,external_id" },
                { value: "orders", label: "Orders", cols: "customer_email,customer_name,amount,order_date" },
                { value: "feedback", label: "Email Feedback", cols: "email,name,subject,body,sentiment,received_at" },
              ].map((t) => (
                <button key={t.value} onClick={() => setImportType(t.value)}
                  className={`px-3 py-1.5 text-xs rounded-lg border ${
                    importType === t.value ? "border-primary bg-primary/10" : "border-border"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mb-2">
              CSV columns: <code className="font-mono">{importType === "crm" ? "email,name,phone,external_id" : importType === "orders" ? "customer_email,customer_name,amount,order_date,description" : "email,name,subject,body,sentiment,received_at"}</code>
            </p>
            <textarea
              className="w-full min-h-[150px] bg-background border border-border rounded p-3 text-xs font-mono"
              placeholder="Paste CSV data here..."
              value={csvData}
              onChange={(e) => setCsvData(e.target.value)}
            />
            <div className="flex justify-end mt-2">
              <Button size="sm" onClick={handleImport} disabled={!csvData.trim()}>Import</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {funnel && (
        <div className="grid grid-cols-5 gap-4">
          {[
            { label: "Total Customers", value: funnel.total_customers, color: "text-blue-400" },
            { label: "Reviewed", value: funnel.reviewed, color: "text-emerald-400" },
            { label: "Chat Sessions", value: funnel.chatted, color: "text-purple-400" },
            { label: "Support Tickets", value: funnel.ticketed, color: "text-amber-400" },
            { label: "Total Revenue", value: `$${funnel.total_revenue.toLocaleString()}`, color: "text-emerald-400" },
          ].map((item) => (
            <Card key={item.label}>
              <CardContent className="pt-6 text-center">
                <p className={`text-2xl font-bold ${item.color}`}>{item.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{item.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4 border-b border-border">
        <button onClick={() => setTab("funnel")} className={`pb-2 text-sm font-medium border-b-2 ${tab === "funnel" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>Funnel</button>
        <button onClick={() => setTab("segments")} className={`pb-2 text-sm font-medium border-b-2 ${tab === "segments" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>Segments</button>
        <button onClick={() => setTab("insights")} className={`pb-2 text-sm font-medium border-b-2 ${tab === "insights" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>AI Insights ({insights.length})</button>
        <button onClick={() => setTab("profiles")} className={`pb-2 text-sm font-medium border-b-2 ${tab === "profiles" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>Profiles ({profiles.length})</button>
      </div>

      {tab === "funnel" && funnel && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Engagement Funnel (90 days)</CardTitle>
            <CardDescription>Customer progression from awareness to support</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center gap-2">
              {[
                { label: "Total Customers", value: funnel.total_customers, pct: 100, color: "bg-blue-400" },
                { label: "Left a Review", value: funnel.reviewed, pct: funnel.total_customers > 0 ? Math.round((funnel.reviewed / funnel.total_customers) * 100) : 0, color: "bg-emerald-400" },
                { label: "Used Chat", value: funnel.chatted, pct: funnel.total_customers > 0 ? Math.round((funnel.chatted / funnel.total_customers) * 100) : 0, color: "bg-purple-400" },
                { label: "Opened Ticket", value: funnel.ticketed, pct: funnel.total_customers > 0 ? Math.round((funnel.ticketed / funnel.total_customers) * 100) : 0, color: "bg-amber-400" },
              ].map((stage, i) => (
                <div key={stage.label} className="w-full max-w-md">
                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                    <span>{stage.label}</span>
                    <span>{stage.value} ({stage.pct}%)</span>
                  </div>
                  <div className="h-5 w-full bg-accent rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-500 ${stage.color}`} style={{ width: `${stage.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {tab === "segments" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Customer Segmentation</CardTitle>
            <CardDescription>Auto-classified customer segments based on behavior and spending</CardDescription>
          </CardHeader>
          <CardContent>
            {funnel && Object.keys(funnel.segment_breakdown).length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(funnel.segment_breakdown).map(([seg, count]) => (
                  <Card key={seg}>
                    <CardContent className="p-4 text-center">
                      <Badge className={SEGMENT_COLORS[seg] || "text-muted-foreground"}>{seg}</Badge>
                      <p className="text-2xl font-bold text-foreground mt-2">{count as number}</p>
                      <p className="text-xs text-muted-foreground">customers</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                No segments yet. Click "Run Segmentation" to classify your customers.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {tab === "insights" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">AI Root-Cause Analysis</CardTitle>
                <CardDescription>Automated analysis of review trends, support patterns, and recommendations</CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={handleAnalyze}>Refresh</Button>
            </div>
          </CardHeader>
          <CardContent>
            {insights.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No analysis yet. Click "AI Analysis" to generate insights.
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {insights.map((ins, i) => (
                  <div key={i} className="border border-border rounded-lg p-4">
                    <div className="flex items-start gap-2">
                      <Badge variant="outline" className={severityColor(ins.severity)}>{ins.severity}</Badge>
                      <div className="flex-1">
                        <p className="font-medium text-sm">{ins.title}</p>
                        <p className="text-xs text-muted-foreground mt-1">{ins.detail}</p>
                        {ins.recommendation && (
                          <p className="text-xs text-primary mt-1">→ {ins.recommendation}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === "profiles" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Customer Profiles</CardTitle>
                <CardDescription>{profiles.length} profiles loaded</CardDescription>
              </div>
              <select
                className="bg-background border border-border rounded px-2 py-1 text-xs"
                value={segmentFilter}
                onChange={(e) => setSegmentFilter(e.target.value)}
              >
                <option value="">All Segments</option>
                <option value="promoter">Promoter</option>
                <option value="high_value">High Value</option>
                <option value="at_risk">At Risk</option>
                <option value="detractor">Detractor</option>
                <option value="new">New</option>
                <option value="lost">Lost</option>
              </select>
            </div>
          </CardHeader>
          <CardContent>
            {profiles.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No profiles found. Import CRM data to get started.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="pb-2 font-medium">Name</th>
                      <th className="pb-2 font-medium">Email</th>
                      <th className="pb-2 font-medium">Segment</th>
                      <th className="pb-2 font-medium text-right">Orders</th>
                      <th className="pb-2 font-medium text-right">Spent</th>
                      <th className="pb-2 font-medium text-right">Churn Risk</th>
                      <th className="pb-2 font-medium text-right">Last Active</th>
                    </tr>
                  </thead>
                  <tbody>
                    {profiles.map((p) => (
                      <tr key={p.id} className="border-b border-border/50">
                        <td className="py-2 font-medium">{p.name || "—"}</td>
                        <td className="py-2 text-muted-foreground">{p.email || "—"}</td>
                        <td className="py-2">
                          {p.segment ? <Badge className={SEGMENT_COLORS[p.segment] || ""}>{p.segment}</Badge> : "—"}
                        </td>
                        <td className="py-2 text-right">{p.total_orders}</td>
                        <td className="py-2 text-right">${p.total_spent.toFixed(2)}</td>
                        <td className="py-2 text-right">
                          <span className={p.churn_risk_score > 0.7 ? "text-rose-400" : p.churn_risk_score > 0.4 ? "text-amber-400" : "text-emerald-400"}>
                            {Math.round(p.churn_risk_score * 100)}%
                          </span>
                        </td>
                        <td className="py-2 text-right text-xs text-muted-foreground">
                          {p.last_activity_at ? new Date(p.last_activity_at).toLocaleDateString() : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
