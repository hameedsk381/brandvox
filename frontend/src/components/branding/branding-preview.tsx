"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useBrandingStore } from "@/stores/branding-store";
import { LayoutDashboard, MessageSquare, BarChart3, Settings } from "lucide-react";

export default function BrandingPreview() {
  const config = useBrandingStore((state) => state.brandingConfig);
  const brandName = config?.company_name || "ReputationOS AI";
  const primary = config?.primary_color || "#6366f1";
  const secondary = config?.secondary_color || "#8b5cf6";

  return (
    <Card>
      <CardHeader><CardTitle>Live Preview</CardTitle></CardHeader>
      <CardContent>
        <div className="rounded-xl border border-border overflow-hidden bg-background">
          {/* Mini Sidebar */}
          <div className="flex">
            <div className="w-20 min-h-[300px] p-3 border-r border-border flex flex-col items-center gap-3" style={{ backgroundColor: `${primary}08` }}>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xs" style={{ backgroundColor: primary }}>
                R
              </div>
              {[LayoutDashboard, MessageSquare, BarChart3, Settings].map((Icon, i) => (
                <div key={i} className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ color: i === 0 ? primary : "#52525b", backgroundColor: i === 0 ? `${primary}15` : "transparent" }}>
                  <Icon className="w-4 h-4" />
                </div>
              ))}
            </div>
            {/* Mini Content */}
            <div className="flex-1 p-4 flex flex-col gap-2">
              <div className="text-xs font-bold" style={{ color: primary }}>{brandName}</div>
              <div className="h-2 w-24 rounded-full" style={{ backgroundColor: `${primary}30` }} />
              <div className="h-2 w-32 rounded-full bg-muted" />
              <div className="h-2 w-20 rounded-full bg-muted" />
              <div className="flex gap-1 mt-2">
                <div className="h-6 w-12 rounded" style={{ backgroundColor: `${primary}20` }} />
                <div className="h-6 w-12 rounded" style={{ backgroundColor: `${secondary}20` }} />
                <div className="h-6 w-12 rounded" style={{ backgroundColor: "#27272a" }} />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-3 p-3 rounded-lg bg-muted/50 border border-border">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold" style={{ background: `linear-gradient(135deg, ${primary}, ${secondary})` }}>
            R
          </div>
          <div>
            <div className="text-sm font-semibold text-foreground">{brandName}</div>
            <div className="text-[10px] text-muted-foreground">White-label preview</div>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <div className="w-6 h-6 rounded border border-border" style={{ backgroundColor: primary }} title="Primary" />
          <div className="w-6 h-6 rounded border border-border" style={{ backgroundColor: secondary }} title="Secondary" />
          <div className="w-6 h-6 rounded border border-border" style={{ backgroundColor: config?.accent_color || "#06b6d4" }} title="Accent" />
        </div>
      </CardContent>
    </Card>
  );
}
