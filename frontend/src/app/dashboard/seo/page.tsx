"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/stores/auth-store";
import toast from "react-hot-toast";

interface SeoProfile {
  id: string; location_id: string; gbp_completeness_score: number;
  gbp_missing_fields: string[]; gbp_photo_count: number;
  gbp_post_count: number; gbp_response_rate: number;
  last_audit_at: string | null;
}

interface KeywordItem {
  id: string; keyword: string; current_rank: number | null;
  previous_rank: number | null; search_volume: string | null;
  last_checked_at: string | null;
}

interface CitationItem {
  id: string; directory_name: string; url: string | null;
  nap_consistent: boolean; issues: string[];
  last_checked_at: string | null;
}

interface AuditResult {
  location_id: string; completeness_score: number;
  missing_fields: string[]; photo_count: number; post_count: number;
  response_rate: number; recommendations: string[];
}

interface Location {
  id: string; name: string; address: string | null;
}

export default function SeoPage() {
  const user = useAuthStore((state) => state.user);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<string>("");
  const [profile, setProfile] = useState<SeoProfile | null>(null);
  const [keywords, setKeywords] = useState<KeywordItem[]>([]);
  const [citations, setCitations] = useState<CitationItem[]>([]);
  const [mapsRankings, setMapsRankings] = useState<any[]>([]);
  const [postSchedules, setPostSchedules] = useState<any[]>([]);
  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [newKeyword, setNewKeyword] = useState("");
  const [newKeywordRank, setNewKeywordRank] = useState("");
  const [tab, setTab] = useState<string>("audit");

  useEffect(() => {
    api.get("/api/locations").then((res) => setLocations(res.data)).catch(() => {});
  }, []);

  const loadSeoData = async (locationId: string) => {
    setLoading(true);
    try {
      const [profRes, kwRes, citRes, mapRes, postRes] = await Promise.all([
        api.get(`/api/seo/profile?location_id=${locationId}`),
        api.get(`/api/seo/keywords?location_id=${locationId}`),
        api.get(`/api/seo/citations?location_id=${locationId}`),
        api.get(`/api/seo/maps-rankings?location_id=${locationId}`),
        api.get(`/api/seo/posts?location_id=${locationId}`),
      ]);
      setProfile(profRes.data);
      setKeywords(kwRes.data);
      setCitations(citRes.data);
      setMapsRankings(mapRes.data);
      setPostSchedules(postRes.data);
    } catch { toast.error("Failed to load SEO data"); }
    finally { setLoading(false); }
  };

  const handleLocationChange = (id: string) => {
    setSelectedLocation(id);
    if (id) loadSeoData(id);
    else { setProfile(null); setKeywords([]); setCitations([]); setAudit(null); }
  };

  const handleRunAudit = async () => {
    if (!selectedLocation) return;
    try {
      const res = await api.get(`/api/seo/audit?location_id=${selectedLocation}`);
      setAudit(res.data);
      toast.success("Audit complete");
      await loadSeoData(selectedLocation);
    } catch { toast.error("Failed to run audit"); }
  };

  const handleCheckCitations = async () => {
    if (!selectedLocation) return;
    try {
      const res = await api.post(`/api/seo/citations/check?location_id=${selectedLocation}`);
      setCitations(res.data);
      toast.success("Citation check complete");
    } catch { toast.error("Failed to check citations"); }
  };

  const handleAddKeyword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyword.trim() || !selectedLocation) return;
    try {
      await api.post(`/api/seo/keywords?location_id=${selectedLocation}`, {
        keyword: newKeyword.trim(),
        current_rank: newKeywordRank ? parseInt(newKeywordRank) : null,
      });
      toast.success("Keyword added");
      setNewKeyword(""); setNewKeywordRank("");
      await loadSeoData(selectedLocation);
    } catch { toast.error("Failed to add keyword"); }
  };

  const handleUpdateRank = async (kwId: string, rank: number) => {
    if (!selectedLocation) return;
    try {
      await api.patch(`/api/seo/keywords/${kwId}?location_id=${selectedLocation}&current_rank=${rank}`);
      await loadSeoData(selectedLocation);
      toast.success("Rank updated");
    } catch { toast.error("Failed to update rank"); }
  };

  const handleDeleteKeyword = async (kwId: string) => {
    if (!confirm("Delete this keyword?")) return;
    try {
      await api.delete(`/api/seo/keywords/${kwId}?location_id=${selectedLocation}`);
      await loadSeoData(selectedLocation);
      toast.success("Keyword deleted");
    } catch { toast.error("Failed to delete"); }
  };

  const scoreColor = (s: number) => {
    if (s >= 80) return "text-emerald-400";
    if (s >= 50) return "text-amber-400";
    return "text-rose-400";
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Local SEO Intelligence</h1>
        <p className="text-sm text-muted-foreground mt-1">Audit your Google Business Profile, track keywords, and monitor citations</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Location</CardTitle>
          <CardDescription>Select a location to view and manage its SEO profile</CardDescription>
        </CardHeader>
        <CardContent>
          <select
            className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm"
            value={selectedLocation}
            onChange={(e) => handleLocationChange(e.target.value)}
          >
            <option value="">Select a location...</option>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>{l.name}{l.address ? ` — ${l.address}` : ""}</option>
            ))}
          </select>
        </CardContent>
      </Card>

      {selectedLocation && loading && <p className="text-sm text-muted-foreground">Loading...</p>}

      {selectedLocation && !loading && (
        <>
          {profile && (
            <div className="grid grid-cols-4 gap-4">
              <Card><CardContent className="p-4 text-center">
                <p className={`text-2xl font-bold ${scoreColor(profile.gbp_completeness_score)}`}>{profile.gbp_completeness_score}%</p>
                <p className="text-xs text-muted-foreground mt-1">GBP Completeness</p>
              </CardContent></Card>
              <Card><CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-foreground">{profile.gbp_photo_count}</p>
                <p className="text-xs text-muted-foreground mt-1">Photos</p>
              </CardContent></Card>
              <Card><CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-foreground">{profile.gbp_post_count}</p>
                <p className="text-xs text-muted-foreground mt-1">Posts</p>
              </CardContent></Card>
              <Card><CardContent className="p-4 text-center">
                <p className={`text-2xl font-bold ${profile.gbp_response_rate >= 80 ? "text-emerald-400" : "text-amber-400"}`}>{profile.gbp_response_rate}%</p>
                <p className="text-xs text-muted-foreground mt-1">Response Rate</p>
              </CardContent></Card>
            </div>
          )}

          <div className="flex items-center gap-4 border-b border-border">
            <button onClick={() => setTab("audit")} className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === "audit" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>Audit & Recommendations</button>
            <button onClick={() => setTab("keywords")} className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === "keywords" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>Keywords ({keywords.length})</button>
            <button onClick={() => setTab("citations")} className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === "citations" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>Citations ({citations.length})</button>
            <button onClick={() => setTab("maps")} className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === "maps" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>Maps Visibility ({mapsRankings.length})</button>
            <button onClick={() => setTab("posts")} className={`pb-2 text-sm font-medium border-b-2 transition-colors ${tab === "posts" ? "border-primary text-foreground" : "border-transparent text-muted-foreground"}`}>Post Scheduler ({postSchedules.length})</button>
          </div>

          {tab === "audit" && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Google Business Profile Audit</CardTitle>
                    <CardDescription>Check completeness and get AI-powered recommendations</CardDescription>
                  </div>
                  <Button size="sm" onClick={handleRunAudit}>Run Audit</Button>
                </div>
              </CardHeader>
              <CardContent>
                {!audit ? (
                  <p className="text-sm text-muted-foreground text-center py-4">Run an audit to see your GBP completeness score and recommendations.</p>
                ) : (
                  <div className="flex flex-col gap-4">
                    {audit.missing_fields.length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-rose-400 mb-2">Missing Fields ({audit.missing_fields.length})</p>
                        <div className="flex flex-wrap gap-2">
                          {audit.missing_fields.map((f) => <Badge key={f} variant="outline" className="text-rose-400 border-rose-400/30">{f}</Badge>)}
                        </div>
                      </div>
                    )}
                    <div>
                      <p className="text-xs font-medium text-foreground mb-2">Recommendations</p>
                      <ul className="flex flex-col gap-2">
                        {audit.recommendations.map((r, i) => (
                          <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-primary mt-0.5">•</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {tab === "keywords" && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Keyword Rankings</CardTitle>
                <CardDescription>Track local search rankings for your key terms</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAddKeyword} className="flex items-end gap-2 mb-4">
                  <div className="flex-1">
                    <Input label="Keyword" placeholder='e.g. "best pizza Brooklyn"' value={newKeyword} onChange={(e) => setNewKeyword(e.target.value)} />
                  </div>
                  <div className="w-24">
                    <Input label="Rank" placeholder="3" type="number" value={newKeywordRank} onChange={(e) => setNewKeywordRank(e.target.value)} />
                  </div>
                  <Button type="submit" disabled={!newKeyword.trim()}>Add</Button>
                </form>

                {keywords.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">No keywords tracked yet. Add your first keyword above.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border text-left text-muted-foreground">
                          <th className="pb-2 font-medium">Keyword</th>
                          <th className="pb-2 font-medium text-right">Current Rank</th>
                          <th className="pb-2 font-medium text-right">Previous</th>
                          <th className="pb-2 font-medium text-right">Search Volume</th>
                          <th className="pb-2 font-medium text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {keywords.map((kw) => {
                          const change = kw.current_rank !== null && kw.previous_rank !== null ? kw.previous_rank - kw.current_rank : 0;
                          return (
                            <tr key={kw.id} className="border-b border-border/50">
                              <td className="py-2 font-medium">{kw.keyword}</td>
                              <td className="py-2 text-right">
                                <input
                                  type="number"
                                  className="w-16 bg-background border border-border rounded px-2 py-1 text-right text-sm"
                                  value={kw.current_rank ?? ""}
                                  onChange={(e) => {
                                    const v = parseInt(e.target.value);
                                    if (!isNaN(v)) handleUpdateRank(kw.id, v);
                                  }}
                                />
                              </td>
                              <td className="py-2 text-right">
                                {kw.previous_rank !== null ? (
                                  <span className={change > 0 ? "text-emerald-400" : change < 0 ? "text-rose-400" : ""}>
                                    {kw.previous_rank} {change > 0 ? "↑" : change < 0 ? "↓" : "—"}
                                  </span>
                                ) : "—"}
                              </td>
                              <td className="py-2 text-right text-muted-foreground">{kw.search_volume || "—"}</td>
                              <td className="py-2 text-right">
                                <Button size="sm" variant="ghost" className="text-rose-400" onClick={() => handleDeleteKeyword(kw.id)}>Del</Button>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {tab === "maps" && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Google Maps Competitor Visibility</CardTitle>
                    <CardDescription>See how your competitors rank on Google Maps for key search terms</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {mapsRankings.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No competitor map rankings yet. Track rankings for your competitors to see Maps visibility.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border text-left text-muted-foreground">
                          <th className="pb-2 font-medium">Competitor</th>
                          <th className="pb-2 font-medium">Keyword</th>
                          <th className="pb-2 font-medium text-right">Maps Rank</th>
                          <th className="pb-2 font-medium text-right">Change</th>
                          <th className="pb-2 font-medium text-right">Last Checked</th>
                        </tr>
                      </thead>
                      <tbody>
                        {mapsRankings.map((mr: any) => {
                          const change = mr.previous_rank !== null ? mr.previous_rank - mr.rank : 0;
                          return (
                            <tr key={mr.id} className="border-b border-border/50">
                              <td className="py-2 font-medium">{mr.competitor_name}</td>
                              <td className="py-2 text-muted-foreground">{mr.keyword}</td>
                              <td className="py-2 text-right">{mr.rank ?? "—"}</td>
                              <td className="py-2 text-right">
                                {change !== 0 ? (
                                  <span className={change > 0 ? "text-emerald-400" : "text-rose-400"}>
                                    {change > 0 ? `+${change}` : change}
                                  </span>
                                ) : "—"}
                              </td>
                              <td className="py-2 text-right text-xs text-muted-foreground">
                                {mr.last_checked_at ? new Date(mr.last_checked_at).toLocaleDateString() : "—"}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {tab === "posts" && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">GBP Post & Photo Scheduler</CardTitle>
                    <CardDescription>Schedule Google Business Profile posts and track photo uploads</CardDescription>
                  </div>
                  <Button size="sm" onClick={async () => {
                    const title = prompt("Post title:");
                    if (!title) return;
                    const desc = prompt("Description (optional):");
                    try {
                      await api.post(`/api/seo/posts?location_id=${selectedLocation}`, {
                        content_type: "post",
                        title,
                        description: desc || undefined,
                      });
                      toast.success("Post scheduled");
                      await loadSeoData(selectedLocation);
                    } catch { toast.error("Failed to create post"); }
                  }}>Schedule Post</Button>
                </div>
              </CardHeader>
              <CardContent>
                {postSchedules.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No posts scheduled yet. Schedule photos and posts to keep your GBP active.
                  </p>
                ) : (
                  <div className="flex flex-col gap-3">
                    {postSchedules.map((p: any) => (
                      <div key={p.id} className="border border-border rounded-lg p-4 flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{p.title || "Untitled"}</span>
                            <Badge variant="outline" className="text-xs">{p.content_type}</Badge>
                            {p.is_published && <Badge className="text-xs bg-emerald-500/10 text-emerald-400 border-emerald-500/20">Published</Badge>}
                          </div>
                          {p.description && <p className="text-xs text-muted-foreground mt-1">{p.description}</p>}
                          <p className="text-xs text-muted-foreground mt-1">
                            {p.scheduled_date ? `Scheduled: ${new Date(p.scheduled_date).toLocaleDateString()}` : "No date set"}
                          </p>
                        </div>
                        <div className="flex gap-1">
                          {!p.is_published && (
                            <Button size="sm" variant="outline" onClick={async () => {
                              try {
                                await api.patch(`/api/seo/posts/${p.id}?location_id=${selectedLocation}&is_published=true`);
                                toast.success("Marked as published");
                                await loadSeoData(selectedLocation);
                              } catch { toast.error("Failed"); }
                            }}>Mark Published</Button>
                          )}
                          <Button size="sm" variant="ghost" className="text-rose-400" onClick={async () => {
                            if (!confirm("Delete this post?")) return;
                            try {
                              await api.delete(`/api/seo/posts/${p.id}?location_id=${selectedLocation}`);
                              await loadSeoData(selectedLocation);
                              toast.success("Deleted");
                            } catch { toast.error("Failed"); }
                          }}>Del</Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {tab === "citations" && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Citation / NAP Monitoring</CardTitle>
                    <CardDescription>Check NAP consistency across business directories</CardDescription>
                  </div>
                  <Button size="sm" onClick={handleCheckCitations}>Check All</Button>
                </div>
              </CardHeader>
              <CardContent>
                {citations.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-4">Run a citation check to see NAP consistency across directories.</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border text-left text-muted-foreground">
                          <th className="pb-2 font-medium">Directory</th>
                          <th className="pb-2 font-medium">NAP Consistent</th>
                          <th className="pb-2 font-medium">Issues</th>
                          <th className="pb-2 font-medium text-right">Last Checked</th>
                        </tr>
                      </thead>
                      <tbody>
                        {citations.map((c) => (
                          <tr key={c.id} className="border-b border-border/50">
                            <td className="py-2 font-medium">{c.directory_name}</td>
                            <td className="py-2">
                              {c.nap_consistent ? (
                                <Badge variant="outline" className="text-emerald-400 border-emerald-400/30">Consistent</Badge>
                              ) : (
                                <Badge variant="outline" className="text-rose-400 border-rose-400/30">Issues Found</Badge>
                              )}
                            </td>
                            <td className="py-2 text-xs text-muted-foreground">
                              {c.issues.length > 0 ? c.issues.join("; ") : "—"}
                            </td>
                            <td className="py-2 text-right text-xs text-muted-foreground">
                              {c.last_checked_at ? new Date(c.last_checked_at).toLocaleDateString() : "—"}
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
        </>
      )}
    </div>
  );
}
