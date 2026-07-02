"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { reportsAPI, ReportFormat, ReportType } from "@/lib/api";
import { FileText, Download } from "lucide-react";
import toast from "react-hot-toast";

export default function ReportsPage() {
  const [loading, setLoading] = useState<string | null>(null);

  const downloadReport = async (format: ReportFormat, type: ReportType) => {
    setLoading(`${format}-${type}`);
    try {
      const blob = await reportsAPI.download(format, type);
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

  const reports = [
    { type: "summary", label: "Reputation Summary", desc: "Overall scores, sentiment distribution, and trends" },
    { type: "reviews", label: "Reviews Report", desc: "All reviews with ratings, sentiment, and replies" },
    { type: "sentiment", label: "Sentiment Analysis", desc: "Deep-dive into sentiment, emotions, and topics" },
  ];

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Reports</h1>
        <p className="text-sm text-muted-foreground mt-1">Generate and download reports</p>
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
                onClick={() => downloadReport("pdf", report.type as ReportType)}
                loading={loading === `pdf-${report.type}`}
              >
                <Download className="w-3.5 h-3.5 mr-1" /> PDF
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => downloadReport("xlsx", report.type as ReportType)}
                loading={loading === `xlsx-${report.type}`}
              >
                <Download className="w-3.5 h-3.5 mr-1" /> Excel
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => downloadReport("pptx", report.type as ReportType)}
                loading={loading === `pptx-${report.type}`}
              >
                <Download className="w-3.5 h-3.5 mr-1" /> PowerPoint
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
