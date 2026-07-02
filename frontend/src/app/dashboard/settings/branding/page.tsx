"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import BrandingForm from "@/components/branding/branding-form";
import BrandingPreview from "@/components/branding/branding-preview";
import { useBrandingStore } from "@/stores/branding-store";

export default function BrandingPage() {
  const config = useBrandingStore((state) => state.brandingConfig);

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">White-Label Branding</h1>
        <p className="text-sm text-muted-foreground mt-1">Customize the look and feel of your agency</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BrandingForm />
        <BrandingPreview />
      </div>
    </div>
  );
}
