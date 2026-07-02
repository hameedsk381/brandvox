"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card, CardContent, CardHeader, CardTitle, CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import toast from "react-hot-toast";

const CAMPAIGN_TYPES = [
  { value: "qr", label: "QR Code", desc: "In-store QR posters and flyers" },
  { value: "nfc", label: "NFC Card", desc: "Tap-to-review NFC business cards" },
  { value: "sms", label: "SMS", desc: "Text message review requests" },
  { value: "email", label: "Email", desc: "Email review request campaigns" },
  { value: "whatsapp", label: "WhatsApp", desc: "WhatsApp review requests" },
];

interface Campaign {
  id: string; name: string; campaign_type: string;
  target_url: string | null; redirect_url: string | null;
  is_active: boolean; total_sent: number;
  total_opened: number; total_converted: number;
  created_at: string;
}

interface Dashboard {
  total_campaigns: number; total_sent: number;
  total_converted: number; active_campaigns: number;
  conversion_rate: number;
  recent_campaigns: { id: string; name: string; campaign_type: string; total_sent: number; total_converted: number; }[];
}

interface LeaderEntry {
  employee_name: string; requests_sent: number;
  conversions: number; conversion_rate: number;
}

export default function ReviewCampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [campaignType, setCampaignType] = useState("qr");
  const [showForm, setShowForm] = useState(false);
  const [qrData, setQrData] = useState<{ id: string; data: string } | null>(null);
  const [contacts, setContacts] = useState("");
  const [showContacts, setShowContacts] = useState<string | null>(null);
  const [tab, setTab] = useState<"campaigns" | "leaderboard">("campaigns");

  const load = async () => {
    try {
      const [cRes, dRes, lRes] = await Promise.all([
        api.get("/api/campaigns"),
        api.get("/api/campaigns/dashboard"),
        api.get("/api/campaigns/leaderboard"),
      ]);
      setCampaigns(cRes.data);
      setDashboard(dRes.data);
      setLeaderboard(lRes.data);
    } catch {
      toast.error("Failed to load campaigns");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await api.post("/api/campaigns", { name: name.trim(), campaign_type: campaignType });
      toast.success("Campaign created");
      setName("");
      setShowForm(false);
      await load();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to create campaign");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this campaign?")) return;
    try {
      await api.delete(`/api/campaigns/${id}`);
      await load();
      toast.success("Deleted");
    } catch {
      toast.error("Failed to delete");
    }
  };

  const handleGenerateQr = async (id: string) => {
    try {
      const res = await api.get(`/api/campaigns/${id}/qr`);
      setQrData({ id, data: res.data.qr_code });
    } catch {
      toast.error("Failed to generate QR code");
    }
  };

  const handleSend = async (id: string) => {
    try {
      const res = await api.post(`/api/campaigns/${id}/send`);
      toast.success(`Sent to ${res.data.sent} contacts${res.data.failed > 0 ? ` (${res.data.failed} failed)` : ""}`);
      await load();
    } catch {
      toast.error("Failed to send");
    }
  };

  const handleAddContacts = async (id: string) => {
    const lines = contacts.split("\n").filter(Boolean);
    const items = lines.map((line) => {
      const parts = line.split(",").map((s) => s.trim());
      const recipient = parts[0];
      const channel = parts[1] || "sms";
      const employee_name = parts[2] || null;
      return { recipient, channel, employee_name };
    });
    if (items.length === 0) return;
    try {
      await api.post(`/api/campaigns/${id}/contacts`, { contacts: items });
      toast.success(`${items.length} contacts added`);
      setContacts("");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to add contacts");
    }
  };

  const typeLabel = (t: string) => CAMPAIGN_TYPES.find((ct) => ct.value === t)?.label || t;

  if (loading) return <div className="p-8 text-muted-foreground">Loading campaigns...</div>;

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Review Campaigns</h1>
          <p className="text-sm text-muted-foreground mt-1">Generate more reviews with QR codes, SMS, email, and WhatsApp</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "New Campaign"}</Button>
      </div>

      {dashboard && (
        <div className="grid grid-cols-4 gap-4">
          {[
            { label: "Total Campaigns", value: dashboard.total_campaigns },
            { label: "Total Sent", value: dashboard.total_sent },
            { label: "Total Converted", value: dashboard.total_converted },
            { label: "Conversion Rate", value: `${dashboard.conversion_rate}%` },
          ].map((s) => (
            <Card key={s.label}>
              <CardContent className="p-4 text-center">
                <p className="text-2xl font-bold text-foreground">{s.value}</p>
                <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Create Campaign</CardTitle>
            <CardDescription>Choose a campaign type to get started</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="flex flex-col gap-4">
              <div className="grid grid-cols-5 gap-2">
                {CAMPAIGN_TYPES.map((ct) => (
                  <button
                    key={ct.value} type="button"
                    onClick={() => setCampaignType(ct.value)}
                    className={`p-3 rounded-lg border text-left text-sm transition-colors ${
                      campaignType === ct.value
                        ? "border-primary bg-primary/10"
                        : "border-border hover:border-primary/50"
                    }`}
                  >
                    <div className="font-medium">{ct.label}</div>
                    <div className="text-xs text-muted-foreground mt-1">{ct.desc}</div>
                  </button>
                ))}
              </div>
              <Input label="Campaign Name" placeholder="e.g. Q4 Review Drive" value={name} onChange={(e) => setName(e.target.value)} required />
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancel</Button>
                <Button type="submit" disabled={!name.trim()}>Create Campaign</Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {qrData && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">QR Code</CardTitle>
            <CardDescription>Download or print this QR code for in-store placement</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4">
            <img src={`data:image/png;base64,${qrData.data}`} alt="QR Code" className="w-48 h-48" />
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => {
                const a = document.createElement("a");
                a.href = `data:image/png;base64,${qrData.data}`;
                a.download = `qr-${qrData.id}.png`;
                a.click();
              }}>Download PNG</Button>
              <Button size="sm" variant="outline" onClick={() => setQrData(null)}>Close</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-4 border-b border-border">
        <button
          onClick={() => setTab("campaigns")}
          className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
            tab === "campaigns" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Campaigns ({campaigns.length})
        </button>
        <button
          onClick={() => setTab("leaderboard")}
          className={`pb-2 text-sm font-medium border-b-2 transition-colors ${
            tab === "leaderboard" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Employee Leaderboard
        </button>
      </div>

      {tab === "campaigns" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All Campaigns</CardTitle>
          </CardHeader>
          <CardContent>
            {campaigns.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">No campaigns yet. Create your first one above.</p>
            ) : (
              <div className="flex flex-col gap-3">
                {campaigns.map((c) => (
                  <div key={c.id} className="border border-border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{c.name}</span>
                          <Badge variant="outline" className="text-xs">{typeLabel(c.campaign_type)}</Badge>
                          {!c.is_active && <Badge variant="secondary" className="text-xs">Inactive</Badge>}
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                          <span>Sent: {c.total_sent}</span>
                          <span>Opened: {c.total_opened}</span>
                          <span>Converted: {c.total_converted}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {c.campaign_type === "qr" && (
                          <Button size="sm" variant="outline" onClick={() => handleGenerateQr(c.id)}>QR</Button>
                        )}
                        {c.campaign_type !== "qr" && c.campaign_type !== "nfc" && (
                          <>
                            <Button size="sm" variant="outline" onClick={() => setShowContacts(showContacts === c.id ? null : c.id)}>
                              Contacts
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleSend(c.id)}>Send</Button>
                          </>
                        )}
                        <Button size="sm" variant="ghost" className="text-rose-400" onClick={() => handleDelete(c.id)}>Delete</Button>
                      </div>
                    </div>

                    {showContacts === c.id && (
                      <div className="mt-3 pt-3 border-t border-border">
                        <p className="text-xs text-muted-foreground mb-2">
                          One per line: <code className="font-mono">recipient,channel,employee_name</code>
                        </p>
                        <div className="flex gap-2">
                          <textarea
                            className="flex-1 min-h-[80px] bg-background border border-border rounded px-3 py-2 text-xs font-mono"
                            placeholder={`+1234567890,sms,John\nuser@example.com,email\n+9876543210,whatsapp,Jane`}
                            value={contacts}
                            onChange={(e) => setContacts(e.target.value)}
                          />
                        </div>
                        <div className="flex justify-end mt-2">
                          <Button size="sm" onClick={() => handleAddContacts(c.id)} disabled={!contacts.trim()}>Add Contacts</Button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === "leaderboard" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Employee Leaderboard</CardTitle>
            <CardDescription>Top performers for review generation this period</CardDescription>
          </CardHeader>
          <CardContent>
            {leaderboard.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No data yet. Tag employee names when adding contacts (recipient,channel,employee_name) to track performance.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="pb-2 font-medium">#</th>
                      <th className="pb-2 font-medium">Employee</th>
                      <th className="pb-2 font-medium text-right">Requests Sent</th>
                      <th className="pb-2 font-medium text-right">Conversions</th>
                      <th className="pb-2 font-medium text-right">Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboard.map((e, i) => (
                      <tr key={e.employee_name} className="border-b border-border/50">
                        <td className="py-2 text-muted-foreground">{i + 1}</td>
                        <td className="py-2 font-medium">{e.employee_name}</td>
                        <td className="py-2 text-right">{e.requests_sent}</td>
                        <td className="py-2 text-right">{e.conversions}</td>
                        <td className="py-2 text-right">{e.conversion_rate}%</td>
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
