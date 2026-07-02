"use client";

import React, { useState, useEffect } from "react";
import { useAuthStore } from "@/stores/auth-store";
import { useBrandingStore } from "@/stores/branding-store";
import { useMutation } from "@tanstack/react-query";
import { settingsAPI } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import ColorPicker from "./color-picker";
import LogoUploader from "./logo-uploader";
import toast from "react-hot-toast";

export default function BrandingForm() {
  const user = useAuthStore((state) => state.user);
  const config = useBrandingStore((state) => state.brandingConfig);
  const setBranding = useBrandingStore((state) => state.setBranding);

  const [form, setForm] = useState({
    company_name: "",
    primary_color: "#6366f1",
    secondary_color: "#8b5cf6",
    accent_color: "#06b6d4",
    font_family: "Inter",
    dark_mode_default: true,
    sidebar_style: "modern",
    logo_url: "",
    favicon_url: "",
  });

  useEffect(() => {
    if (config) {
      setForm({
        company_name: config.company_name || "",
        primary_color: config.primary_color || "#6366f1",
        secondary_color: config.secondary_color || "#8b5cf6",
        accent_color: config.accent_color || "#06b6d4",
        font_family: config.font_family || "Inter",
        dark_mode_default: config.dark_mode_default ?? true,
        sidebar_style: config.sidebar_style || "modern",
        logo_url: config.logo_url || "",
        favicon_url: config.favicon_url || "",
      });
    }
  }, [config]);

  const saveMutation = useMutation({
    mutationFn: () => {
      const targetAgencyId = user?.agency_id || config?.agency_id;
      if (!targetAgencyId) throw new Error("No agency");
      return settingsAPI.updateBranding(targetAgencyId, form);
    },
    onSuccess: (data) => {
      setBranding(data);
      toast.success("Branding updated");
    },
    onError: () => toast.error("Failed to save branding"),
  });

  return (
    <Card>
      <CardHeader><CardTitle>Branding Configuration</CardTitle></CardHeader>
      <CardContent className="flex flex-col gap-5">
        <Input
          label="Company Name"
          placeholder="Your Brand Name"
          value={form.company_name}
          onChange={(e) => setForm({ ...form, company_name: e.target.value })}
        />

        <LogoUploader />

        <div className="grid grid-cols-3 gap-3">
          <ColorPicker
            label="Primary"
            value={form.primary_color}
            onChange={(v) => setForm({ ...form, primary_color: v })}
          />
          <ColorPicker
            label="Secondary"
            value={form.secondary_color}
            onChange={(v) => setForm({ ...form, secondary_color: v })}
          />
          <ColorPicker
            label="Accent"
            value={form.accent_color}
            onChange={(v) => setForm({ ...form, accent_color: v })}
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Font</label>
          <select
            className="w-full h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
            value={form.font_family}
            onChange={(e) => setForm({ ...form, font_family: e.target.value })}
          >
            <option value="Inter">Inter</option>
            <option value="Outfit">Outfit</option>
            <option value="Plus Jakarta Sans">Plus Jakarta Sans</option>
            <option value="DM Sans">DM Sans</option>
          </select>
        </div>

        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1 block">Sidebar Style</label>
          <select
            className="w-full h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/60"
            value={form.sidebar_style}
            onChange={(e) => setForm({ ...form, sidebar_style: e.target.value })}
          >
            <option value="modern">Modern</option>
            <option value="classic">Classic</option>
            <option value="minimal">Minimal</option>
          </select>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Dark Mode Default</span>
          <Switch
            checked={form.dark_mode_default}
            onCheckedChange={(v) => setForm({ ...form, dark_mode_default: v })}
          />
        </div>

        <Button onClick={() => saveMutation.mutate()} loading={saveMutation.isPending}>
          Save Branding
        </Button>
      </CardContent>
    </Card>
  );
}
