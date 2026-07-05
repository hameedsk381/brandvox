"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTenantStore } from "@/stores/tenant-store";
import { useAuthStore } from "@/stores/auth-store";
import { competitorsAPI, api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Trophy, 
  Trash2, 
  Sparkles, 
  Plus, 
  AlertCircle, 
  TrendingUp, 
  TrendingDown, 
  PlusCircle, 
  RotateCw, 
  ThumbsUp, 
  ThumbsDown, 
  Lightbulb,
  CheckCircle,
  HelpCircle,
  XCircle,
  Star,
  DollarSign,
  FileText
} from "lucide-react";
import toast from "react-hot-toast";

export default function CompetitorsPage() {
  const queryClient = useQueryClient();
  const currentLocation = useTenantStore((state) => state.currentLocation);
  const user = useAuthStore((state) => state.user);

  const [newCompName, setNewCompName] = useState("");
  const [googlePlaceId, setGooglePlaceId] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [weeklyReport, setWeeklyReport] = useState<any>(null);

  // Fetch competitors
  const { data: competitors, isLoading: isLoadingComp } = useQuery({
    queryKey: ["competitors", currentLocation?.id],
    queryFn: () => competitorsAPI.list(currentLocation!.id),
    enabled: !!currentLocation?.id,
  });

  // Fetch comparative analytics
  const { data: analytics, isLoading: isLoadingAnalytics } = useQuery({
    queryKey: ["competitor-analytics", currentLocation?.id],
    queryFn: () => competitorsAPI.getAnalytics(currentLocation!.id),
    enabled: !!currentLocation?.id,
  });

  // Fetch AI analysis
  const { data: aiAnalysis, isLoading: isLoadingAnalysis } = useQuery({
    queryKey: ["competitor-analysis", currentLocation?.id],
    queryFn: () => competitorsAPI.getAnalysis(currentLocation!.id),
    enabled: !!currentLocation?.id,
  });

  // Mutation to add competitor
  const addMutation = useMutation({
    mutationFn: () => competitorsAPI.create(currentLocation!.id, newCompName, googlePlaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["competitors"] });
      queryClient.invalidateQueries({ queryKey: ["competitor-analytics"] });
      setNewCompName("");
      setGooglePlaceId("");
      setIsAdding(false);
      toast.success("Competitor added and reviews synced!");
    },
    onError: () => toast.error("Failed to add competitor"),
  });

  // Mutation to delete competitor
  const deleteMutation = useMutation({
    mutationFn: (id: string) => competitorsAPI.delete(currentLocation!.id, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["competitors"] });
      queryClient.invalidateQueries({ queryKey: ["competitor-analytics"] });
      toast.success("Competitor deleted");
    },
    onError: () => toast.error("Failed to delete competitor"),
  });

  // Mutation to trigger AI analysis
  const analyzeMutation = useMutation({
    mutationFn: () => competitorsAPI.triggerAnalysis(currentLocation!.id),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["competitor-analysis"] });
      toast.success("AI competitor analysis updated!");
    },
    onError: () => toast.error("Failed to run analysis"),
  });

  const handleAddCompetitor = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompName.trim()) return;
    addMutation.mutate();
  };

  const isWriteAuthorized = user?.role === "super_admin" || user?.role === "agency_admin" || user?.role === "client_admin" || user?.role === "marketing_manager";

  if (!currentLocation) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-muted-foreground">
        <Trophy className="w-16 h-16 opacity-20 mb-4" />
        <h3 className="text-lg font-medium text-foreground">Select a location</h3>
        <p className="text-sm">Please select a business location to load competitor intelligence.</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Competitor Intelligence</h1>
          <p className="text-sm text-muted-foreground mt-1">Benchmark and analyze competitors for {currentLocation.name}</p>
        </div>
        
        {isWriteAuthorized && (
          <Button 
            onClick={() => analyzeMutation.mutate()} 
            loading={analyzeMutation.isPending} 
            disabled={!competitors || competitors.length === 0}
            className="w-full md:w-auto shadow-sm"
          >
            <Sparkles className="w-4 h-4 mr-2" /> Run AI Comparison
          </Button>
        )}
      </div>

      {/* Sample-data disclaimer: competitor reviews are seeded templates until
          a real data source is connected. Never let this render as real intel. */}
      {analytics?.is_sample_data && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-600 dark:text-amber-400">
          <span className="font-semibold">Sample data:</span> competitor metrics and AI analysis below are
          generated from illustrative sample reviews, not real competitor data. Do not share them with clients
          as competitive intelligence.
        </div>
      )}

      {/* Grid: Stats and List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Competitor List & Admin Panel */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          {/* Add Competitor */}
          {isWriteAuthorized && (
            <Card className="border-border">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <PlusCircle className="w-4 h-4 text-primary" /> Add Competitor
                </CardTitle>
                <CardDescription>Track another local business</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAddCompetitor} className="flex flex-col gap-3">
                  <Input 
                    placeholder="Competitor Name (e.g. Burger joint Uptown)" 
                    value={newCompName} 
                    onChange={(e) => setNewCompName(e.target.value)}
                    required
                  />
                  <Input 
                    placeholder="Google Place ID (optional)" 
                    value={googlePlaceId} 
                    onChange={(e) => setGooglePlaceId(e.target.value)}
                  />
                  <Button type="submit" loading={addMutation.isPending} size="sm" className="w-full">
                    Add & Seed Reviews
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}

          {/* Competitors List */}
          <Card className="border-border flex-1">
            <CardHeader>
              <CardTitle className="text-base">Competitors List</CardTitle>
              <CardDescription>Currently tracking {competitors?.length || 0} competitors</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {isLoadingComp ? (
                <div className="flex items-center justify-center py-8">
                  <RotateCw className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : !competitors || competitors.length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-8">No competitors added yet. Use the card above to add competitors.</p>
              ) : (
                competitors.map((comp: any) => (
                  <div key={comp.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 border border-border">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded bg-primary/10 flex items-center justify-center text-primary font-bold text-xs uppercase">
                        {comp.name.slice(0, 2)}
                      </div>
                      <div className="text-xs font-semibold text-foreground">{comp.name}</div>
                    </div>
                    {isWriteAuthorized && (
                      <button 
                        onClick={() => deleteMutation.mutate(comp.id)}
                        className="p-1 rounded text-muted-foreground hover:text-rose-500 hover:bg-rose-500/10 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Comparative Charts */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <Card className="border-border">
            <CardHeader>
              <CardTitle className="text-base">Comparative Diagnostics</CardTitle>
              <CardDescription>Compare review performance side-by-side</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-6">
              {isLoadingAnalytics ? (
                <div className="flex items-center justify-center py-16">
                  <RotateCw className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : !analytics || (analytics.competitors.length === 0 && analytics.client.review_count === 0) ? (
                <div className="text-center py-16 text-muted-foreground text-sm flex flex-col items-center gap-2">
                  <AlertCircle className="w-8 h-8 opacity-25" />
                  <span>No analytics data available. Please add competitors first.</span>
                </div>
              ) : (
                <div className="flex flex-col gap-6">
                  {/* Rating comparison bars */}
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Average Star Rating</h4>
                    <div className="flex flex-col gap-3">
                      {/* Client */}
                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between text-xs font-medium">
                          <span>{analytics.client.name}</span>
                          <span className="flex items-center text-emerald-400 font-bold">{analytics.client.avg_rating} <Star className="w-3 h-3 fill-emerald-400 text-emerald-400 ml-0.5" /></span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2 overflow-hidden border border-border">
                          <div 
                            className="bg-primary h-full rounded-full transition-all duration-500" 
                            style={{ width: `${(analytics.client.avg_rating / 5) * 100}%` }}
                          />
                        </div>
                      </div>
                      {/* Competitors */}
                      {analytics.competitors.map((c: any) => (
                        <div key={c.id} className="flex flex-col gap-1">
                          <div className="flex justify-between text-xs font-medium">
                            <span>{c.name}</span>
                            <span className="flex items-center font-bold">{c.avg_rating} <Star className="w-3 h-3 fill-primary/80 text-primary/80 ml-0.5" /></span>
                          </div>
                          <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
                            <div 
                              className="bg-muted-foreground/45 h-full rounded-full transition-all duration-500" 
                              style={{ width: `${(c.avg_rating / 5) * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Sentiment distribution grid */}
                  <div>
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Sentiment Distribution</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Client card */}
                      <div className="p-4 rounded-xl border border-border bg-muted/10">
                        <div className="text-xs font-bold text-foreground mb-3">{analytics.client.name}</div>
                        <div className="flex flex-col gap-2">
                          {Object.entries(analytics.client.sentiment_distribution).map(([s, count]: any) => {
                            const total = analytics.client.review_count || 1;
                            const pct = Math.round((count / total) * 100);
                            return (
                              <div key={s} className="flex items-center gap-2 text-xs">
                                <span className="w-16 capitalize text-muted-foreground">{s}</span>
                                <div className="flex-1 bg-muted rounded-full h-1.5 overflow-hidden">
                                  <div 
                                    className={`h-full rounded-full ${s === 'positive' ? 'bg-emerald-500' : s === 'negative' ? 'bg-rose-500' : s === 'mixed' ? 'bg-amber-500' : 'bg-zinc-400'}`}
                                    style={{ width: `${pct}%` }}
                                  />
                                </div>
                                <span className="w-8 text-right font-medium">{pct}%</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Competitors cards */}
                      {analytics.competitors.slice(0, 1).map((c: any) => (
                        <div key={c.id} className="p-4 rounded-xl border border-border bg-muted/10">
                          <div className="text-xs font-bold text-foreground mb-3">{c.name}</div>
                          <div className="flex flex-col gap-2">
                            {Object.entries(c.sentiment_distribution).map(([s, count]: any) => {
                              const total = c.review_count || 1;
                              const pct = Math.round((count / total) * 100);
                              return (
                                <div key={s} className="flex items-center gap-2 text-xs">
                                  <span className="w-16 capitalize text-muted-foreground">{s}</span>
                                  <div className="flex-1 bg-muted rounded-full h-1.5 overflow-hidden">
                                    <div 
                                      className={`h-full rounded-full ${s === 'positive' ? 'bg-emerald-500' : s === 'negative' ? 'bg-rose-500' : s === 'mixed' ? 'bg-amber-500' : 'bg-zinc-400'}`}
                                      style={{ width: `${pct}%` }}
                                    />
                                  </div>
                                  <span className="w-8 text-right font-medium">{pct}%</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Pricing Tracking & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-border">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" /> Pricing Intelligence
            </CardTitle>
            <CardDescription>Track competitor pricing changes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              {!competitors || competitors.length === 0 ? (
                <p className="text-xs text-muted-foreground text-center py-4">Add competitors to track pricing.</p>
              ) : (
                competitors.map((comp: any) => (
                  <PriceTracker key={comp.id} competitor={comp} locationId={currentLocation.id} />
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400" /> Intelligence Alerts
                </CardTitle>
                <CardDescription>New locations, campaigns, and expansion signals</CardDescription>
              </div>
              <Button size="sm" variant="outline" onClick={async () => {
                const name = prompt("Competitor name:");
                if (!name) return;
                const type = prompt("Alert type (new_location / campaign / expansion):") || "new_location";
                const desc = prompt("Description:");
                try {
                  await api.post(`/api/competitors/alerts?competitor_name=${encodeURIComponent(name)}&alert_type=${type}&description=${encodeURIComponent(desc || "")}`);
                  queryClient.invalidateQueries({ queryKey: ["competitor-alerts"] });
                  toast.success("Alert created");
                } catch { toast.error("Failed"); }
              }}>+ Alert</Button>
            </div>
          </CardHeader>
          <CardContent>
            <AlertsList locationId={currentLocation.id} />
          </CardContent>
        </Card>
      </div>

      {/* Weekly Report */}
      <Card className="border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" /> Weekly Competitor Report
              </CardTitle>
              <CardDescription>AI-generated competitive intelligence summary</CardDescription>
            </div>
            <Button size="sm" variant="outline" onClick={async () => {
              try {
                const res = await api.get(`/api/competitors/weekly-report?location_id=${currentLocation.id}`);
                setWeeklyReport(res.data);
                toast.success("Report generated");
              } catch { toast.error("Failed to generate report"); }
            }}>Generate Report</Button>
          </div>
        </CardHeader>
        <CardContent>
          {!weeklyReport ? (
            <p className="text-sm text-muted-foreground text-center py-4">Generate a weekly report to see AI-powered competitive insights.</p>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="grid grid-cols-3 gap-4">
                <Card><CardContent className="p-3 text-center"><p className="text-lg font-bold">{weeklyReport.total_competitors}</p><p className="text-xs text-muted-foreground">Competitors</p></CardContent></Card>
                <Card><CardContent className="p-3 text-center"><p className="text-lg font-bold">{weeklyReport.competitors?.length || 0}</p><p className="text-xs text-muted-foreground">Tracked</p></CardContent></Card>
                <Card><CardContent className="p-3 text-center"><p className="text-lg font-bold">{weeklyReport.report_date}</p><p className="text-xs text-muted-foreground">Report Date</p></CardContent></Card>
              </div>
              {weeklyReport.ai_insights?.summary && (
                <div className="p-4 rounded-lg bg-primary/5 border border-primary/10">
                  <p className="text-xs font-medium text-primary mb-1">AI Summary</p>
                  <p className="text-sm text-muted-foreground">{weeklyReport.ai_insights.summary}</p>
                  {weeklyReport.ai_insights.top_threat && (
                    <p className="text-xs text-rose-400 mt-2">⚠ {weeklyReport.ai_insights.top_threat}</p>
                  )}
                  {weeklyReport.ai_insights.top_opportunity && (
                    <p className="text-xs text-emerald-400 mt-1">✓ {weeklyReport.ai_insights.top_opportunity}</p>
                  )}
                </div>
              )}
              {weeklyReport.competitors?.map((c: any) => (
                <div key={c.name} className="border border-border rounded-lg p-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm">{c.name}</span>
                    <span className="text-xs text-muted-foreground">{c.avg_rating ? `${c.avg_rating}★` : "—"} · {c.review_count} reviews</span>
                  </div>
                  {c.price_changes?.length > 0 && (
                    <div className="mt-2 flex flex-col gap-1">
                      <p className="text-xs font-medium text-muted-foreground">Recent price changes:</p>
                      {c.price_changes.map((p: any, i: number) => (
                        <p key={i} className="text-xs text-amber-400">${p.price} — {p.note || "No note"}</p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* AI Action Board / Report Analysis */}
      <Card className="border-border bg-background/5 backdrop-blur-xl dark:bg-[#0a0a0f]/50">
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary animate-pulse" /> AI Competitor Intelligence Insights
          </CardTitle>
          <CardDescription>Groq-powered comparison audit of customer reviews</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingAnalysis ? (
            <div className="flex items-center justify-center py-8">
              <RotateCw className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : !aiAnalysis ? (
            <div className="text-center py-8 text-muted-foreground text-sm flex flex-col items-center gap-2 border border-dashed border-border rounded-xl">
              <AlertCircle className="w-8 h-8 opacity-25" />
              <span>No AI analysis run yet for this location. Click "Run AI Comparison" above to generate insights.</span>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {/* Summary */}
              <div className="p-4 rounded-xl bg-primary/5 border border-primary/10">
                <h4 className="text-xs font-bold text-primary uppercase tracking-wider mb-1.5">Executive Summary</h4>
                <p className="text-xs text-muted-foreground dark:text-muted-foreground leading-relaxed">{aiAnalysis.summary}</p>
              </div>

              {/* Strengths & Weaknesses */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Strengths */}
                <div className="flex flex-col gap-2.5">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 uppercase tracking-wider">
                    <ThumbsUp className="w-4 h-4" /> Competitive Strengths
                  </div>
                  <div className="flex flex-col gap-2">
                    {aiAnalysis.strengths.map((str: string, index: number) => (
                      <div key={index} className="flex items-start gap-2 p-3 rounded-lg border border-emerald-500/10 bg-emerald-500/5 text-xs text-foreground">
                        <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{str}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Weaknesses */}
                <div className="flex flex-col gap-2.5">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-rose-400 uppercase tracking-wider">
                    <ThumbsDown className="w-4 h-4" /> Competitive Weaknesses
                  </div>
                  <div className="flex flex-col gap-2">
                    {aiAnalysis.weaknesses.map((weak: string, index: number) => (
                      <div key={index} className="flex items-start gap-2 p-3 rounded-lg border border-rose-500/10 bg-rose-500/5 text-xs text-foreground">
                        <XCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                        <span>{weak}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Opportunities */}
              <div className="flex flex-col gap-2.5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-cyan-400 uppercase tracking-wider">
                  <Lightbulb className="w-4 h-4" /> Market Opportunities & Recommendations
                </div>
                <div className="flex flex-col gap-2">
                  {aiAnalysis.opportunities.map((opp: string, index: number) => (
                    <div key={index} className="flex items-start gap-2.5 p-3 rounded-lg border border-cyan-500/10 bg-cyan-500/5 text-xs text-foreground">
                      <HelpCircle className="w-4 h-4 text-cyan-500 shrink-0 mt-0.5" />
                      <span>{opp}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PriceTracker({ competitor, locationId }: { competitor: any; locationId: string }) {
  const [price, setPrice] = useState("");
  const [note, setNote] = useState("");
  const { data: prices, refetch } = useQuery({
    queryKey: ["competitor-prices", competitor.id],
    queryFn: () => api.get(`/api/competitors/prices?competitor_id=${competitor.id}`).then(r => r.data),
  });

  const recordPrice = async () => {
    if (!price) return;
    try {
      await api.post(`/api/competitors/prices?competitor_id=${competitor.id}&price=${parseFloat(price)}${note ? `&description=${encodeURIComponent(note)}` : ""}`);
      toast.success("Price recorded");
      setPrice("");
      setNote("");
      refetch();
    } catch { toast.error("Failed"); }
  };

  const changes = Array.isArray(prices) ? prices : prices?.prices || prices?.changes || [];

  return (
    <div className="border border-border rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{competitor.name}</span>
        <span className="text-xs text-muted-foreground">{changes.length} recorded</span>
      </div>
      <div className="flex gap-2 mb-2">
        <Input placeholder="Price ($)" value={price} onChange={e => setPrice(e.target.value)} className="w-24 text-xs" />
        <Input placeholder="Note (optional)" value={note} onChange={e => setNote(e.target.value)} className="flex-1 text-xs" />
        <Button size="sm" variant="outline" onClick={recordPrice}><DollarSign className="w-3 h-3" /></Button>
      </div>
      {changes.length > 0 && (
        <div className="flex flex-col gap-1 max-h-24 overflow-y-auto">
          {changes.slice(-5).reverse().map((p: any, i: number) => (
            <p key={i} className="text-xs text-muted-foreground">
              <span className="font-medium">${p.price}</span>
              {p.note && <span> — {p.note}</span>}
              <span className="ml-1 opacity-50">{p.recorded_at ? new Date(p.recorded_at).toLocaleDateString() : ""}</span>
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

function AlertsList({ locationId }: { locationId: string }) {
  const { data: alerts, isLoading } = useQuery({
    queryKey: ["competitor-alerts"],
    queryFn: () => api.get("/api/competitors/alerts").then(r => r.data),
  });

  if (isLoading) return <div className="flex justify-center py-4"><RotateCw className="w-5 h-5 animate-spin" /></div>;

  const items = Array.isArray(alerts) ? alerts : alerts?.alerts || [];

  if (items.length === 0) return <p className="text-xs text-muted-foreground text-center py-4">No alerts yet.</p>;

  return (
    <div className="flex flex-col gap-2 max-h-64 overflow-y-auto">
      {items.map((a: any, i: number) => (
        <div key={a.id || i} className="flex items-start gap-2 p-2 rounded-lg border border-border text-xs">
          <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${a.alert_type === "new_location" ? "bg-blue-500/20 text-blue-400" : a.alert_type === "campaign" ? "bg-amber-500/20 text-amber-400" : "bg-rose-500/20 text-rose-400"}`}>
            {a.alert_type === "new_location" ? "NL" : a.alert_type === "campaign" ? "CA" : "EX"}
          </div>
          <div>
            <p className="font-medium">{a.competitor_name}</p>
            <p className="text-muted-foreground">{a.description || a.alert_type.replace("_", " ")}</p>
            <p className="text-[10px] text-muted-foreground/50">{a.created_at ? new Date(a.created_at).toLocaleDateString() : ""}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
