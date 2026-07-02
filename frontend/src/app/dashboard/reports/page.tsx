"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { reportsAPI, ReportFormat, ReportType, scheduledReportsAPI, ScheduledReportItem } from "@/lib/api";
import { FileText, Download, Clock, Plus, Trash2, ToggleLeft, ToggleRight } from "lucide-react";
import toast from "react-hot-toast";

export default function ReportsPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [schedules, setSchedules] = useState<ScheduledReportItem[]>([]);
  const [schedulesLoading, setSchedulesLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formName, setFormName] = useState("");
  const [formType, setFormType] = useState("monthly");
  const [formFormat, setFormFormat] = useState("pdf");

  useEffect(() => {
    loadSchedules();
  }, []);

  const loadSchedules = async () => {
    try {
      setSchedulesLoading(true);
      const data = await scheduledReportsAPI.list();
      setSchedules(data);
    } catch {
      // Schedules endpoint may not exist yet in all deployments
      setSchedules([]);
    } finally {
      setSchedulesLoading(false);
    }
  };

  const downloadReport = async (format: ReportFormat, type: string) => {
    setLoading(`${format}-${type}`);
    try {
      const blob = await reportsAPI.download(format, type as ReportType);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${type}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success("Report downloaded");
    } catch {
      toast.error("Failed to download report");
    } finally {
      setLoading(null);
    }
  };

  const createSchedule = async () => {
    if (!formName.trim()) return;
    try {
      await scheduledReportsAPI.create({
        name: formName.trim(),
        report_type: formType,
        format: formFormat,
      });
      toast.success("Scheduled report created");
      setShowForm(false);
      setFormName("");
      await loadSchedules();
    } catch {
      toast.error("Failed to create scheduled report");
    }
  };

  const toggleSchedule = async (item: ScheduledReportItem) => {
    try {
      await scheduledReportsAPI.update(item.id, { is_active: !item.is_active });
      toast.success(item.is_active ? "Schedule paused" : "Schedule activated");
      await loadSchedules();
    } catch {
      toast.error("Failed to update schedule");
    }
  };

  const deleteSchedule = async (id: string) => {
    try {
      await scheduledReportsAPI.delete(id);
      toast.success("Schedule deleted");
      await loadSchedules();
    } catch {
      toast.error("Failed to delete schedule");
    }
  };

  const reports = [
    { type: "summary", label: "Reputation Summary", desc: "Overall scores, sentiment distribution, and trends" },
    { type: "reviews", label: "Reviews Report", desc: "All reviews with ratings, sentiment, and replies" },
    { type: "sentiment", label: "Sentiment Analysis", desc: "Deep-dive into sentiment, emotions, and topics" },
  ];

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Reports</h1>
          <p className="text-sm text-muted-foreground mt-1">Generate, download, and schedule reports</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reports.map((report) => (
          <Card key={report.type}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-primary" />
                <CardTitle className="text-sm">{report.label}</CardTitle>
              </div>
              <CardDescription>{report.desc}</CardDescription>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => downloadReport("pdf", report.type)}
                loading={loading === `pdf-${report.type}`}
              >
                <Download className="w-3.5 h-3.5 mr-1" /> PDF
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => downloadReport("xlsx", report.type)}
                loading={loading === `xlsx-${report.type}`}
              >
                <Download className="w-3.5 h-3.5 mr-1" /> Excel
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => downloadReport("pptx", report.type)}
                loading={loading === `pptx-${report.type}`}
              >
                <Download className="w-3.5 h-3.5 mr-1" /> PowerPoint
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-background/5 backdrop-blur-xl border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              <CardTitle>Scheduled Reports</CardTitle>
            </div>
            <Button size="sm" onClick={() => setShowForm(true)}>
              <Plus className="w-3.5 h-3.5 mr-1" /> New schedule
            </Button>
          </div>
          <CardDescription>Automatically generate reports on a recurring basis.</CardDescription>
        </CardHeader>
        <CardContent>
          {schedulesLoading ? (
            <p className="text-sm text-muted-foreground">Loading schedules...</p>
          ) : schedules.length === 0 ? (
            <div className="text-center py-6">
              <p className="text-sm text-muted-foreground">No scheduled reports yet.</p>
              <p className="text-xs text-muted-foreground mt-1">Click "New schedule" to set up automatic report generation.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {schedules.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-border bg-muted/30"
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground">{item.name}</span>
                      <span className="text-[10px] uppercase text-muted-foreground px-1.5 py-0.5 rounded bg-muted border border-border">
                        {item.format}
                      </span>
                      <span className="text-[10px] uppercase text-muted-foreground px-1.5 py-0.5 rounded bg-muted border border-border">
                        {item.report_type}
                      </span>
                      {!item.is_active && (
                        <span className="text-[10px] text-amber-400 font-medium">Paused</span>
                      )}
                    </div>
                    {item.last_sent_at && (
                      <span className="text-xs text-muted-foreground">
                        Last sent: {new Date(item.last_sent_at).toLocaleDateString()}
                      </span>
                    )}
                    {item.is_active && item.next_run_at && (
                      <span className="text-xs text-muted-foreground">
                        Next run: {new Date(item.next_run_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => toggleSchedule(item)}
                      title={item.is_active ? "Pause" : "Activate"}
                    >
                      {item.is_active ? <ToggleRight className="w-4 h-4 text-emerald-400" /> : <ToggleLeft className="w-4 h-4" />}
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      onClick={() => deleteSchedule(item.id)}
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4 text-muted-foreground hover:text-rose-400" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-background rounded-xl border border-border p-6 w-full max-w-md shadow-2xl">
            <h3 className="font-semibold mb-1 text-foreground">New scheduled report</h3>
            <p className="text-xs text-muted-foreground mb-4">Set up automatic report generation on a recurring basis.</p>

            <div className="flex flex-col gap-3">
              <div>
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Name</label>
                <input
                  className="w-full h-9 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
                  placeholder="e.g. Weekly executive summary"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                />
              </div>

              <div>
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Report type</label>
                <select
                  className="w-full h-9 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
                  value={formType}
                  onChange={(e) => setFormType(e.target.value)}
                >
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Format</label>
                <select
                  className="w-full h-9 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
                  value={formFormat}
                  onChange={(e) => setFormFormat(e.target.value)}
                >
                  <option value="pdf">PDF</option>
                  <option value="xlsx">Excel</option>
                  <option value="pptx">PowerPoint</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <Button size="sm" variant="ghost" onClick={() => setShowForm(false)}>Cancel</Button>
              <Button size="sm" onClick={createSchedule} disabled={!formName.trim()}>Create</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
